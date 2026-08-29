# PromptOS Python API

## Compile

```python
from regen_promptos import FoundryRequest, compile_request

request = FoundryRequest.from_dict(
    {
        "source_material": "Repair this broken prompt: make the best app.",
        "operation": "AUTO",
        "task_mode": "DO_NOT_EXECUTE",
        "output_mode": "STANDARD",
        "target_platform": "openai-reasoning",
    }
)

package = compile_request(request)
print(package["runtime_prompt"])
```

## Route without compiling

```python
from regen_promptos import FoundryRequest, route_request

decision = route_request(
    FoundryRequest(source_material="Create a research prompt using primary sources.")
)
print(decision.to_dict())
```

## Deterministic conformance

```python
from regen_promptos import run_conformance

report = run_conformance()
assert report["status"] == "PASS", report["failures"]
```

## Package fields

- `source_sha256`
- `operation`
- `selected_modules`
- `adapter`
- `risk`
- `routing_reasons`
- `pir`
- `runtime_prompt`
- `foundry_completion_state`
- `underlying_project_state`
- `validation`

The API compiles prompt packages. It does not itself execute underlying external actions.
