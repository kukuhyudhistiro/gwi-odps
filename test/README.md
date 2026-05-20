# Tests

Unit tests for the GWi+ODPS pipeline (placeholder).

## Running

```bash
pip install pytest
pytest tests/ -v
```

## Suggested Test Coverage

- `test_gabor_core.py` — GWi kernel construction and pipeline
- `test_nms_odps.py` — ODPS module on synthetic step edges
- `test_evaluation.py` — Berkeley protocol implementation
