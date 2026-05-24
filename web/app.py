"""Pentia v4 — Web UI (FastAPI)
Manejo robusto de errores y validación de entrada
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from starlette.middleware.cors import CORSMiddleware

# Configurar logging
logger = logging.getLogger("pentia.web")
logger.setLevel(logging.INFO)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    model: str = Field(default="qwen2.5-coder", min_length=1, max_length=100)
    memory_enabled: bool = True

    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v.strip()


class CVERequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    service: str = Field(..., min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=50)

    @validator('target')
    def target_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El target no puede estar vacío')
        return v.strip()


class ReconRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    fast: bool = False

    @validator('target')
    def target_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El target no puede estar vacío')
        return v.strip()


class MemoryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    k: int = Field(default=5, ge=1, le=50)

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('La consulta no puede estar vacía')
        return v.strip()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pentia v4",
        version="4.0.0",
        docs_url="/api/docs",
        description="Red Team AI Platform"
    )

    # Agregar CORS para desarrollo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["localhost", "127.0.0.1", "0.0.0.0"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Manejo de errores global ──────────────────────────────────────────

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"error": "Entrada inválida", "detail": str(exc)}
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError):
        logger.error(f"RuntimeError: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor", "detail": str(exc)}
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
                f"<h1>❌ Error al cargar la UI</h1><pre>{str(e)}</pre>",
                status_code=500
            )

    @app.get("/health")
    async def health():
        """Health check para balanceadores"""
        return {
            "status": "ok",
            "version": "4.0.0",
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
                content={"error": "Error interno del servidor"}
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
                content={
                    "error": "Error enriqueciendo CVE",
                    "detail": str(e)
                }
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
                content={"error": f"Módulo no disponible: {e}"}
            )
        except Exception as e:
            logger.error(f"Error en recon: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error ejecutando recon: {str(e)[:200]}"}
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
        except Exception as e:
            logger.error(f"Error en búsqueda de memoria: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error en búsqueda: {str(e)[:200]}"}
            )

    return app


def _check_module_available(module_name: str) -> bool:
    """Verificar si un módulo está disponible"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False
