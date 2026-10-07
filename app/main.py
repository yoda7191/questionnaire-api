from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db import make_engine
from app.models import Base
from app.routers import scales, submissions
from app.scales import load_scales
from app.schemas import Health
from app.scoring import AnswerValidationError

def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = make_engine(settings.database_url)
        Base.metadata.create_all(engine)
        app.state.scales = load_scales(settings.scales_dir)
        app.state.session_factory = sessionmaker(engine, expire_on_commit=False)
        yield
        engine.dispose()

    app = FastAPI(
        title="Questionnaire Scoring API",
        description="Scores standardized psychological questionnaries.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(scales.router)
    app.include_router(submissions.router)

    @app.exception_handler(AnswerValidationError)
    async def answer_validation_handler(request: Request, e: AnswerValidationError):
        return JSONResponse(status_code=422, content={"detail": e.errors})

    @app.get("/health", response_model=Health, tags=["meta"], summary="Liveness check")
    def health():
        return Health(status="ok")

    return app

app = create_app()