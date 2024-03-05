from fastapi import FastAPI, BackgroundTasks
from app.api.auth import register, login
from app.api.chat import chatroom
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import database
import redis
import threading
from threading import Event
from app.core.redis_utils import get_redis_client, listen_for_messages


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# redis_client = redis.Redis(host="redis", port=6379, db=0)


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
app.include_router(chatroom.router, prefix="/chatroom", tags=["chatroom"])


@app.get("/")
async def root():
    return {"message": "Hello Project 1!"}


@app.get("/healthCheck")
async def healthCheck():
    mongoDb = False
    redisDb = False
    try:
        # add key value to redis
        redis_client.set("healthCheck", "redis")
        # get key value from redis
        checkRedis = redis_client.get("healthCheck")
        if checkRedis:
            redisDb = True
    except Exception as e:
        print(e)

    try:
        # check if mongoDb is created collection test
        checkMongo = await database.command("ping")

        if checkMongo:
            mongoDb = True
    except Exception as e:
        print(e)

    if mongoDb and redisDb:
        return {"message": "All services are up and running"}
    else:
        return {
            "message": "Some services are down",
            "mongoDb": mongoDb,
            "redisDb": redisDb,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
