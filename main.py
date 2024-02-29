from fastapi import FastAPI, BackgroundTasks
from app.api.auth import register, login
from fastapi.middleware.cors import CORSMiddleware
import redis
import threading
from threading import Event
import asyncio
import json
from app.core.redis_utils import get_redis_client, listen_for_messages

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# redis_client = redis.Redis(host="localhost", port=6379, db=0)
redis_client = redis.Redis(host="redis-1", port=6379, db=0)


listening_thread_active = True

redis_client = get_redis_client()
listening_thread_active = True

stop_listening_event = Event()


@app.on_event("startup")
async def startup_event():
    global listener_thread
    listener_thread = threading.Thread(
        target=listen_for_messages, args=(redis_client, stop_listening_event)
    )
    listener_thread.start()


@app.on_event("shutdown")
async def shutdown_event():
    stop_listening_event.set()
    listener_thread.join()


app.include_router(register.router, prefix="/auth", tags=["auth"])
app.include_router(login.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Hello Cloud system drive"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
