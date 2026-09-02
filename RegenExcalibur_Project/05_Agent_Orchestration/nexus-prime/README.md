# NEXUS-PRIME embed

Canonical doctrine: https://github.com/Lornt1666/NEXUS-GENESIS-PRIME

This folder is a **sidecar**. It does not join the MRV workflow in `agent_definitions.yaml`.

## Run (dry-run, local only)

```bash
python3 RegenExcalibur_Project/05_Agent_Orchestration/nexus-prime/run_nexus_prime.py --kernel master
python3 RegenExcalibur_Project/05_Agent_Orchestration/nexus-prime/load_kernel.py gem --json
```

Optional, using the existing orchestrator against the sidecar definitions:

```bash
python3 RegenExcalibur_Project/05_Agent_Orchestration/multi_agent_orchestrator.py \
  --definitions RegenExcalibur_Project/05_Agent_Orchestration/nexus-prime/nexus_prime_workflow.yaml \
  --dry-run
```

The generic orchestrator will report `No specialized handler for NexusPrimeAgent` unless you use this sidecar runner. That is expected. Use `run_nexus_prime.py` for a real compile card.

## Install kernels on this machine

```bash
git clone https://github.com/Lornt1666/NEXUS-GENESIS-PRIME.git
bash NEXUS-GENESIS-PRIME/tools/install.sh
```
