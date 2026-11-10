"""Pentia v4 — Web UI (FastAPI)
Manejo robusto de errores y validación de entrada.

Security model (by design, no auth): the UI binds to 127.0.0.1:8000 and
this app additionally rejects any request whose client is not loopback
(see the localhost-only middleware below). CORS is limited to the local
UI origins with credentials disabled. Targets and model names are
validated before any scan or LLM call, and 500 responses never leak
exception details to the client (they are only logged server-side).
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.cors import CORSMiddleware

from core.validation import validate_model_name, validate_target

# Configurar logging
logger = logging.getLogger("pentia.web")
logger.setLevel(logging.INFO)

VERSION = "4.0.2"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    model: str = Field(default="qwen2.5-coder:1.5b", min_length=1, max_length=100)
    memory_enabled: bool = True

    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v.strip()

    @field_validator('model')
    @classmethod
    def model_must_be_valid(cls, v):
        # Model names reach `ollama run` as an argument; allowlist only.
        return validate_model_name(v)


class CVERequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    service: str = Field(..., min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=50)

    @field_validator('target')
    @classmethod
    def target_must_be_valid(cls, v):
        return validate_target(v.strip())


class ReconRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    fast: bool = False

    @field_validator('target')
    @classmethod
    def target_must_be_valid(cls, v):
        return validate_target(v.strip())


class MemoryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    k: int = Field(default=5, ge=1, le=50)

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('La consulta no puede estar vacía')
        return v.strip()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pentia v4",
        version=VERSION,
        docs_url="/api/docs",
        description="Red Team AI Platform"
    )

    # CORS limitado a la UI local; sin credenciales.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # La UI es localhost-only por diseño (sin auth): rechazar cualquier
    # cliente que no sea loopback, aunque el puerto quedara expuesto.
    @app.middleware("http")
    async def localhost_only(request: Request, call_next):
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost"):
            logger.warning(f"Blocked non-localhost request from {client_host} to {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden: this UI is localhost-only"},
            )
        return await call_next(request)

    # Cabeceras de seguridad en todas las respuestas. Nota: ui.html es una
    # app de un solo archivo con <script> inline, handlers onclick y un
    # bloque <style>, por lo que script-src y style-src necesitan
    # 'unsafe-inline' hasta que el JS/CSS se externalice; aun así, la CSP
    # bloquea otros orígenes y el framing/MIME-sniffing quedan cubiertos.
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    # ── Manejo de errores global ──────────────────────────────────────────

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": "Entrada inválida", "detail": str(exc)}
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"error": "Entrada inválida", "detail": str(exc)}
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError):
        # Never leak exception details in 500 responses; log them instead.
        logger.error(f"RuntimeError: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal error"}
        )

    # ── Rutas ─────────────────────────────────────────────────────────────

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """Sirve la interfaz web principal"""
        try:
            html_path = Path(__file__).parent / "ui.html"
            if html_path.exists():
                return HTMLResponse(html_path.read_text(encoding='utf-8'))
            else:
                logger.warning("ui.html no encontrado")
                return HTMLResponse(
                    "<h1>❌ Error: ui.html no encontrado</h1>"
                    "<p>Reinstala el proyecto con: ./install.sh</p>",
                    status_code=404
                )
        except Exception as e:
            logger.error(f"Error sirviendo índice: {e}")
            return HTMLResponse(
                "<h1>❌ Error al cargar la UI</h1>",
                status_code=500
            )

    @app.get("/health")
    async def health():
        """Health check para balanceadores"""
        return {
            "status": "ok",
            "version": VERSION,
            "modules": {
                "ai": _check_module_available("core.ai"),
                "memory": _check_module_available("core.memory"),
                "intel": _check_module_available("core.intel")
            }
        }

    @app.post("/api/chat")
    async def chat(req: ChatRequest):
        """Chat con IA (requiere Ollama)"""
        try:
            from core.ai import LLMClient
            llm = LLMClient(model=req.model)
        except ImportError:
            logger.error("LLMClient no disponible")
            return JSONResponse(
                status_code=503,
                content={
                    "response": "Módulo AI no disponible. Revisa la instalación.",
                    "model": req.model,
                    "error": "OLLAMA_NOT_AVAILABLE"
                }
            )
        except Exception as e:
            logger.error(f"Error inicializando LLMClient: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error"}
            )

        context = None
        if req.memory_enabled:
            try:
                from core.memory import MemoryStore
                mem = MemoryStore()
                items = await mem.retrieve(req.message, k=3)
                if items:
                    context = "\n\n".join(i.get("text", "") for i in items)
                    logger.debug(f"Contexto de memoria: {len(context)} caracteres")
            except Exception as e:
                logger.warning(f"Memoria no disponible: {e}")
                # Continuar sin contexto

        try:
            response = await llm.generate(req.message, context=context)
            return {"response": response, "model": req.model}
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return {
                "response": (
                    f"⚠️ Error generando respuesta del modelo '{req.model}'.\n\n"
                    f"Soluciones:\n"
                    f"  1. ¿Ollama está corriendo?\n"
                    f"     → ollama serve\n"
                    f"  2. ¿El modelo está descargado?\n"
                    f"     → ollama pull {req.model}\n"
                    f"  3. Lista modelos disponibles:\n"
                    f"     → ollama list"
                ),
                "model": req.model,
                "error": "OLLAMA_ERROR"
            }

    @app.post("/api/cve")
    async def cve_enrich(req: CVERequest):
        """Enriquecimiento CVE"""
        try:
            from core.intel import enrich_service
            result = await enrich_service(req.target, req.service, req.version)
            return result
        except ImportError:
            logger.error("Módulo intel no disponible")
            return JSONResponse(
                status_code=503,
                content={"error": "Módulo intel no disponible"}
            )
        except Exception as e:
            logger.error(f"Error en enriquecimiento CVE: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error"}
            )

    @app.post("/api/recon")
    async def recon(req: ReconRequest):
        """Ejecutar recon"""
        try:
            import pipelines.recon as rp
            from core.memory import MemoryStore
            from core.orchestrator import Orchestrator

            memory = MemoryStore()
            orchestrator = Orchestrator()
            results = await rp.run_recon_pipeline(
                req.target, memory, orchestrator, fast=req.fast
            )
            return {
                "target": req.target,
                "results": {k: str(v) for k, v in results.items()}
            }
        except ImportError as e:
            logger.error(f"Módulo faltante: {e}")
            return JSONResponse(
                status_code=503,
                content={"error": "Módulo no disponible"}
            )
        except Exception as e:
            logger.error(f"Error en recon: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error"}
            )

    @app.post("/api/memory/search")
    async def memory_search(req: MemoryRequest):
        """Buscar en memoria"""
        try:
            from core.memory import MemoryStore
            mem = MemoryStore()
            results = await mem.retrieve(req.query, k=req.k)
            return {"results": results, "count": len(results)}
        except ImportError:
            logger.error("Chromadb no disponible")
            return JSONResponse(
                status_code=503,
                content={"error": "Memoria no disponible (Chromadb no instalado)"}
            )
        except RuntimeError as e:
            # MemoryStore raises a clear error when chromadb is absent.
            logger.warning(f"Memoria no disponible: {e}")
            return JSONResponse(
                status_code=503,
                content={"error": "Memoria no disponible (Chromadb no instalado)"}
            )
        except Exception as e:
            logger.error(f"Error en búsqueda de memoria: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error"}
            )

    return app


def _check_module_available(module_name: str) -> bool:
    """Verificar si un módulo está disponible"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False
