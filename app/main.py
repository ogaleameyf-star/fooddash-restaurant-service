"""Restaurant Service - owns restaurants and their menus.

Run locally:  uvicorn app.main:app --reload --port 8001
"""
import logging
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .config import settings
from .database import Base, SessionLocal, engine
from .routes import router
from .seed import seed_if_empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(settings.service_name)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_data:
        with SessionLocal() as db:
            seed_if_empty(db)
    log.info("%s started on pod/host %s", settings.service_name, socket.gethostname())
    yield


app = FastAPI(
    title="FoodDash - Restaurant Service",
    version="1.0.0",
    description="Manages restaurants and menus; validates and prices orders for the Order Service.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health/live", tags=["health"], summary="Liveness probe")
def live():
    return {"status": "UP", "service": settings.service_name}


@app.get("/health/ready", tags=["health"], summary="Readiness probe (checks the database)")
def ready():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    # 'instance' shows which replica answered - useful when scaling on Kubernetes.
    return {"status": "READY", "service": settings.service_name, "instance": socket.gethostname()}
