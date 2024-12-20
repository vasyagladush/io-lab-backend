import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_responses import custom_openapi

from config import app_config, session_manager
from routes.grades import router as GradesRouter
from routes.surveys import router as SurveysRouter
from routes.users import router as UsersRouter

# from routes.debug import router as DebugRouter

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if app_config.DEBUG_LOGS else logging.INFO,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    yield
    if session_manager._engine is not None:
        # Close the DB connection
        await session_manager.close()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None if app_config.ENVIRONMENT == "production" else "/docs",
)
app.openapi = custom_openapi(app)

# TODO: when we have production env set up, add FRONTEND_URL to .env and here if ENVIRONMENT == production then set allow_origin to the FRONTEND_URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=list("*"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Index"])
async def read_root():
    return {"cool": True}


app.include_router(UsersRouter, tags=["Users"], prefix="/users")
app.include_router(SurveysRouter, tags=["Surveys"], prefix="/surveys")
app.include_router(GradesRouter, tags=["Grades"], prefix="/grades")
# app.include_router(DebugRouter, tags=["Debug"], prefix="/debug")
