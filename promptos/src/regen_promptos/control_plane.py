"""Private PromptOS control-plane contract stub (v4.4).

This module implements the *in-memory* control plane that the public client
will eventually call over HTTPS. It is deliberately not a network server:
no sockets, no TLS termination, no database, no payment processor, no hosted
deployment. It exists so the authorization, settlement, cancellation, and
ledger contracts can be tested and schematized before any real infrastructure
is chosen.

Hard invariants preserved from v4.1–v4.3:

* provider keys are never accepted, stored, logged, or returned;
* raw prompts and raw provider outputs are never accepted;
* PromptOS access tokens are represented only as opaque, non-reversible
  hashes — never as plaintext;
* every commercial state transition is idempotent and append-only;
* a failed or expired reservation can never be settled as successful;
* service units are abstract orchestration units, not currency, crypto,
  cash, or provider tokens.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

__all__ = [
    "ControlPlaneError",
    "InMemoryControlPlane",
    "RESERVATION_TTL_S",
]

RESERVATION_TTL_S = 15 * 60  # 15 minutes

_FORBIDDEN_KEYS = {
    "api_key", "apikey", "provider_key", "secret", "password",
    "access_token", "promptos_access_token", "authorization",
    "cookie", "runtime_prompt", "source_material", "output_text",
    "raw_output", "provider_output",
}


class ControlPlaneError(ValueError):
    """Raised when a control-plane operation is unsafe or invalid."""


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _reject_secrets(payload: Mapping[str, Any], where: str) -> None:
    for key in payload:
        normalized = str(key).strip().lower().replace("-", "_")
        if normalized in _FORBIDDEN_KEYS:
            raise ControlPlaneError(
                f"{key!r} is forbidden at the control-plane boundary ({where})"
            )
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for needle in ("sk-", "Bearer ", "x-api-key"):
        if needle in serialized:
            raise ControlPlaneError(
                f"possible secret material detected in {where}"
            )


@dataclass
class _Reservation:
    reservation_id: str
    idempotency_key: str
    account_id: str
    service_units: int
    status: str
    created_at: float
    expires_at: float
    authorization_request: dict[str, Any]
    settlement: dict[str, Any] | None = None


class InMemoryControlPlane:
    """Append-only, idempotent control plane backed by process memory.

    Suitable for deterministic tests and local dry-runs. Not durable across
    process restarts and not a production deployment.
    """

    def __init__(self) -> None:
        self._accounts: dict[str, str] = {}
        self._reservations: dict[str, _Reservation] = {}
        self._by_idempotency: dict[str, str] = {}
        self._ledger: list[dict[str, Any]] = []
        self._revoked: set[str] = set()

    # -- account / token lifecycle ------------------------------------------

    def register_account(self, account_id: str) -> str:
        if not account_id or not isinstance(account_id, str):
            raise ControlPlaneError("account_id is required")
        token = "pt_" + uuid.uuid4().hex
        self._accounts[account_id] = _sha(token)
        return token

    def revoke_token(self, token: str) -> None:
        self._revoked.add(_sha(token))

    def _require_token(self, token: str) -> str:
        digest = _sha(token)
        if digest in self._revoked:
            raise ControlPlaneError("token revoked")
        for account_id, stored in self._accounts.items():
            if stored == digest:
                return account_id
        raise ControlPlaneError("unknown or invalid token")

    # -- authorize ----------------------------------------------------------

    def authorize(
        self,
        token: str,
        authorization_request: Mapping[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        _reject_secrets(authorization_request, "authorize")
        account_id = self._require_token(token)
        key = idempotency_key.strip()
        if not key:
            raise ControlPlaneError("idempotency_key is required")
        if key in self._by_idempotency:
            return self._reservation_view(self._by_idempotency[key])

        units = int(authorization_request.get("service_quote", {}).get("total_units", 0))
        if units <= 0:
            raise ControlPlaneError("service_units must be positive")

        now = time.time()
        reservation = _Reservation(
            reservation_id="res_" + uuid.uuid4().hex[:16],
            idempotency_key=key,
            account_id=account_id,
            service_units=units,
            status="RESERVED",
            created_at=now,
            expires_at=now + RESERVATION_TTL_S,
            authorization_request=dict(authorization_request),
        )
        self._reservations[reservation.reservation_id] = reservation
        self._by_idempotency[key] = reservation.reservation_id
        self._append_ledger(
            "RESERVE",
            reservation.reservation_id,
            account_id,
            units,
            key,
        )
        return self._reservation_view(reservation)

    # -- settle --------------------------------------------------------------

    def settle(
        self,
        token: str,
        reservation_id: str,
        *,
        provider_outcome: str,
        provider_request_id: str | None = None,
        output_sha256: str | None = None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        _require_token = self._require_token(token)
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise ControlPlaneError("unknown reservation")
        if reservation.account_id != _require_token:
            raise ControlPlaneError("reservation does not belong to this account")
        key = idempotency_key.strip()
        if key in self._by_idempotency and self._by_idempotency[key] != reservation_id:
            # idempotency key already used for a different reservation
            return self._reservation_view(self._by_idempotency[key])
        if reservation.status == "SETTLED":
            return self._reservation_view(reservation)
        if reservation.status != "RESERVED":
            raise ControlPlaneError(f"cannot settle reservation in state {reservation.status}")
        if time.time() > reservation.expires_at:
            reservation.status = "EXPIRED"
            self._append_ledger(
                "EXPIRE", reservation_id, reservation.account_id,
                reservation.service_units, key,
            )
            raise ControlPlaneError("reservation expired; settlement refused")
        if provider_outcome != "SUCCEEDED":
            reservation.status = "CANCELLED"
            self._append_ledger(
                "CANCEL_ON_FAILURE", reservation_id, reservation.account_id,
                reservation.service_units, key,
            )
            return self._reservation_view(reservation)

        reservation.status = "SETTLED"
        reservation.settlement = {
            "provider_outcome": provider_outcome,
            "provider_request_id": provider_request_id,
            "output_sha256": output_sha256,
            "settled_at": time.time(),
        }
        self._by_idempotency[key] = reservation_id
        self._append_ledger(
            "SETTLE", reservation_id, reservation.account_id,
            reservation.service_units, key,
        )
        return self._reservation_view(reservation)

    # -- cancel --------------------------------------------------------------

    def cancel(
        self,
        token: str,
        reservation_id: str,
        *,
        idempotency_key: str,
        reason: str = "customer_cancelled",
    ) -> dict[str, Any]:
        account_id = self._require_token(token)
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise ControlPlaneError("unknown reservation")
        if reservation.account_id != account_id:
            raise ControlPlaneError("reservation does not belong to this account")
        key = idempotency_key.strip()
        if reservation.status == "CANCELLED":
            return self._reservation_view(reservation)
        if reservation.status == "SETTLED":
            raise ControlPlaneError("cannot cancel a settled reservation")
        reservation.status = "CANCELLED"
        self._append_ledger(
            "CANCEL", reservation_id, account_id, reservation.service_units, key,
            reason=reason,
        )
        return self._reservation_view(reservation)

    # -- ledger --------------------------------------------------------------

    def ledger(self) -> list[dict[str, Any]]:
        return list(self._ledger)

    def _append_ledger(
        self,
        event: str,
        reservation_id: str,
        account_id: str,
        units: int,
        idempotency_key: str,
        reason: str | None = None,
    ) -> None:
        entry = {
            "event": event,
            "reservation_id": reservation_id,
            "account_id": account_id,
            "service_units": units,
            "idempotency_key": idempotency_key,
            "timestamp": time.time(),
            "sequence": len(self._ledger),
        }
        if reason is not None:
            entry["reason"] = reason
        prev_hash = self._ledger[-1]["entry_hash"] if self._ledger else "0" * 64
        entry["prev_hash"] = prev_hash
        entry["entry_hash"] = _sha(json.dumps(entry, sort_keys=True, default=str))
        self._ledger.append(entry)

    def _reservation_view(self, reservation: _Reservation) -> dict[str, Any]:
        return {
            "reservation_id": reservation.reservation_id,
            "account_id": reservation.account_id,
            "service_units": reservation.service_units,
            "status": reservation.status,
            "created_at": reservation.created_at,
            "expires_at": reservation.expires_at,
            "settlement": reservation.settlement,
            "provider_key_included": False,
            "raw_prompt_included": False,
            "raw_output_included": False,
        }
