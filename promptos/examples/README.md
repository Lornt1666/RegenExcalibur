# Examples

Compile the included request from the `promptos/` directory:

```bash
promptos compile --request examples/request.json --output examples/package.json
```

Inspect these fields first:

- `operation`
- `selected_modules`
- `risk`
- `routing_reasons`
- `pir`
- `validation`
- `runtime_prompt`

The generated package file is intentionally ignored unless it is being preserved as release evidence.
