import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database.session import SessionLocal, database
from app.repositories.json_database import JsonDataError

logger = logging.getLogger("app.main")

_FRONTEND_ROOT = None


def _resolve_frontend() -> Path:
    global _FRONTEND_ROOT
    if _FRONTEND_ROOT is not None:
        return _FRONTEND_ROOT
    settings = get_settings()
    candidates = [
        Path(settings.FRONTEND_DIR),
        Path("..") / "frontend",
        Path(os.path.dirname(__file__)).parent.parent.parent / "frontend",
        Path("frontend"),
    ]
    for cand in candidates:
        if (cand / "index.html").exists():
            _FRONTEND_ROOT = cand.resolve()
            return cand.resolve()
    raise RuntimeError(
        "Diretório do frontend não encontrado. Defina FRONTEND_DIR no .env"
    )


def _run_recurring_job() -> int:
    """Processa recorrencias de todos os usuários e gera notificações."""
    from app.models.user import User
    from app.services.notification_service import NotificationService
    from app.services.recurring_service import RecurringService

    db = SessionLocal()
    total_created = 0
    try:
        user_ids = [u.id for u in db.all(User)]
        for uid in user_ids:
            created = RecurringService(db).process(uid)
            total_created += len(created)
            NotificationService(db).generate(uid)
        db.commit()
        return total_created
    except Exception:
        logger.exception("Falha no job de recorrencias")
        db.rollback()
        return 0
    finally:
        db.close()


async def _background_loop() -> None:
    while True:
        try:
            count = await asyncio.to_thread(_run_recurring_job)
            if count:
                logger.info("Job recorrente gerou %d lançamentos", count)
        except Exception:
            logger.exception("Erro no job recorrente")
        await asyncio.sleep(6 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_background_loop())
    yield
    task.cancel()


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Finaxis — Sistema de Controle Financeiro Pessoal. API REST "
            "documentada automaticamente. Autenticação por JWT e dados "
            "isolados por usuário."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_PREFIX)

    frontend = _resolve_frontend()
    assets_dir = frontend / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="assets",
        )

    @app.get("/login", include_in_schema=False)
    def login_page():
        return FileResponse(str(frontend / "pages" / "login.html"))

    @app.get("/", include_in_schema=False)
    def index_page():
        return FileResponse(str(frontend / "index.html"))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = []
        for error in exc.errors():
            loc = ".".join(str(p) for p in error.get("loc", []))
            details.append(f"{loc}: {error.get('msg', 'valor inválido')}")
        logger.warning("Validação falhou em %s: %s", request.url.path, details)
        return JSONResponse(
            status_code=422,
            content={"detail": details or "Dados inválidos"},
        )

    @app.exception_handler(JsonDataError)
    async def json_data_handler(request: Request, exc: JsonDataError):
        logger.error("Falha de integridade de dados em %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "Falha de integridade nos dados. A operação foi cancelada "
                    "para evitar perda de informação."
                )
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Erro não tratado em %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"},
        )

    @app.get("/health", tags=["Health"])
    def health():
        alive = database.health()
        return {"status": "ok" if alive else "degraded", "app": settings.APP_NAME}

    return app


app = create_app()