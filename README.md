# Benchmarking Async vs Sync FastAPI Endpoints

This repository compares async and sync FastAPI endpoints under concurrent load.

The current app simulates I/O-bound inference using `asyncio.sleep()` and `time.sleep()`, then benchmarks both paths with `hey` to observe throughput and latency differences.

## How to execute

### 1) Start the Uvicorn server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 2) Run load tests with hey

Async endpoint:

```bash
hey -m POST -n 1000 -c 50 "http://localhost:8000/inference_async?x=5"
```

Sync endpoint:

```bash
hey -m POST -n 1000 -c 50 "http://localhost:8000/inference_sync?x=5"
```

### Optional: run the comparison script

```bash
python hey_benchmark.py
```

## Future direction

- Replace simulated waits with real model-inference calls.
- Add agent-style workflows that fan out to multiple model/tool calls.
- Benchmark across worker/process configurations and queueing strategies.
- Add reproducible benchmark reports for production-style deployment setups.