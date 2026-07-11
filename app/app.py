from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .controllers import pagos
from fastapi import FastAPI


app = FastAPI()

app.include_router(pagos.router)