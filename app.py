import time
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.post("/inference_async")
async def inference_async(x: int) -> int:
    # Simulates I/O wait (non-blocking)
    await asyncio.sleep(2)
    return x * 2

@app.post("/inference_sync")
def inference_sync(x: int) -> int:
    # Simulates I/O wait (blocking the worker/thread)
    time.sleep(2)
    return x * 2