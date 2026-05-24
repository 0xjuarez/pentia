import asyncio
import re
import shutil
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

try:
    import ollama
except ImportError:  # pragma: no cover
    ollama = None

logger = logging.getLogger("pentia.ai")
_executor = ThreadPoolExecutor(max_workers=4)


class LLMClient:
    FALLBACK_MODELS = ["qwen2.5:1.5b", "pentia-v2:latest"]
    ANSI_PATTERN = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    SPINNER_PATTERN = re.compile(r"[\u2800-\u28FF\u2580-\u259F]+")

    def __init__(self, model: str = "qwen2.5-coder", temperature: float = 0.1):
        self.model = model
        self.temperature = temperature
        logger.debug(f"LLMClient inicializado con modelo: {model}")

    async def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generar texto con manejo robusto de errores"""
        if not prompt or not prompt.strip():
            logger.warning("Prompt vacío recibido")
            return "Error: El prompt no puede estar vacío"

        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\n{prompt}"

        # Intentar con client Python de Ollama primero
        if ollama is not None:
            try:
                logger.debug("Intentando con ollama Python client")
                return await asyncio.get_running_loop().run_in_executor(
                    _executor, self._ollama_generate, full_prompt
                )
            except Exception as e:
                error_msg = self._clean_output(str(e))
                logger.warning(f"Ollama Python client falló: {error_msg}")
                
                # Si el binario de ollama existe, intentar CLI
                if shutil.which("ollama") is not None:
                    logger.debug("Ollama CLI disponible, intentando fallback")
                    fallback = self._find_fallback_model(exclude=self.model)
                    if fallback:
                        self.model = fallback
                        logger.info(f"Usando modelo fallback: {fallback}")
                        return (
                            f"⚠️ Client Python de Ollama falló. Usando modelo de fallback: {fallback}\n\n"
                            + await asyncio.get_running_loop().run_in_executor(
                                _executor, self._ollama_cli_generate, full_prompt
                            )
                        )
                return f"❌ Error Ollama: {error_msg}\n\nIntenta: ollama serve"

        # Fallback a CLI si el módulo Python no está disponible
        if shutil.which("ollama") is not None:
            logger.debug("Ollama Python no disponible, usando CLI")
            if not self._ollama_model_available():
                fallback = self._find_fallback_model(exclude=self.model)
                if fallback:
                    self.model = fallback
                    logger.info(f"Modelo {self.model} no disponible, usando: {fallback}")
                    return (
                        f"⚠️ Modelo '{self.model}' no estaba disponible. Usando fallback: {fallback}\n\n"
                        + await asyncio.get_running_loop().run_in_executor(
                            _executor, self._ollama_cli_generate, full_prompt
                        )
                    )
                logger.error(f"Modelo '{self.model}' no instalado")
                return (
                    f"❌ Modelo '{self.model}' no instalado.\n\n"
                    f"Descárgalo con:\n"
                    f"  ollama pull {self.model}\n\n"
                    f"O lista modelos disponibles:\n"
                    f"  ollama list"
                )
            return await asyncio.get_running_loop().run_in_executor(
                _executor, self._ollama_cli_generate, full_prompt
            )

        # Sin Ollama disponible
        logger.error("Ollama no está instalado o no es accesible")
        return (
            "❌ Ollama no está disponible.\n\n"
            "Instalación:\n"
            "  1. Descarga desde: https://ollama.com/download\n"
            "  2. Inicia: ollama serve\n"
            "  3. Descarga un modelo: ollama pull qwen2.5-coder\n"
            "  4. Reintenta: pentia chat"
        )

    def _ollama_generate(self, prompt: str) -> str:
        """Llamar API de Ollama via cliente Python"""
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={"temperature": self.temperature}
            )
            return self._clean_output(response.get("response", ""))
        except Exception as e:
            logger.error(f"Error en _ollama_generate: {e}")
            raise

    def _ollama_cli_generate(self, prompt: str) -> str:
        """Fallback a CLI de Ollama"""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.error(f"ollama CLI error: {result.stderr}")
                raise RuntimeError(f"Ollama error: {result.stderr}")
            return self._clean_output(result.stdout)
        except subprocess.TimeoutExpired:
            logger.error("Timeout esperando respuesta de Ollama")
            raise RuntimeError("Timeout (5 min) esperando respuesta de Ollama")
        except Exception as e:
            logger.error(f"Error en _ollama_cli_generate: {e}")
            raise

    def _fallback_generate(self, prompt: str) -> str:
        """Fallback cuando Ollama no está disponible"""
        logger.warning("Usando respuesta placeholder (Ollama no disponible)")
        return (
            "Ollama no está disponible. "
            "Instala desde https://ollama.com/download y ejecuta 'ollama serve'"
        )

    def _clean_output(self, text: str) -> str:
        """Limpiar output de ANSI codes y caracteres de spinner"""
        if text is None:
            return ""
        try:
            clean = self.ANSI_PATTERN.sub("", text)
            clean = self.SPINNER_PATTERN.sub("", clean)
            clean = clean.replace("\r", "")
            clean = re.sub(r"[ \t]+", " ", clean)
            clean = re.sub(r"\n\s*\n+", "\n", clean)
            return clean.strip()
        except Exception as e:
            logger.error(f"Error limpiando output: {e}")
            return text.strip() if text else ""

    def _ollama_model_available(self) -> bool:
        """Verificar si el modelo está disponible en Ollama CLI"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return self.model in result.stdout
        except Exception as e:
            logger.warning(f"Error verificando modelos de Ollama: {e}")
            return False

    def _find_fallback_model(self, exclude: str = "") -> Optional[str]:
        """Encontrar un modelo fallback disponible"""
        for model in self.FALLBACK_MODELS:
            if model != exclude and self._model_exists(model):
                logger.info(f"Modelo fallback encontrado: {model}")
                return model
        logger.warning("No hay modelos fallback disponibles")
        return None

    @staticmethod
    def _model_exists(model: str) -> bool:
        """Verificar si un modelo existe localmente"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return model in result.stdout
        except Exception:
            return False

    def _clean_output(self, text: str) -> str:
        if text is None:
            return ""
        clean = self.ANSI_PATTERN.sub("", text)
        clean = self.SPINNER_PATTERN.sub("", clean)
        clean = clean.replace("\r", "")
        clean = re.sub(r"[ \t]+", " ", clean)
        clean = re.sub(r"\n\s*\n+", "\n", clean)
        return clean.strip()

    def _ollama_generate(self, prompt: str) -> str:
        client = ollama.Ollama()
        response = client.chat(self.model, prompt, temperature=self.temperature)
        return self._clean_output(response.text)

    def _ollama_model_available(self) -> bool:
        try:
            subprocess.run(
                ["ollama", "show", self.model],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return True
        except subprocess.SubprocessError:
            return False

    def _get_installed_models(self) -> List[str]:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            lines = result.stdout.strip().splitlines()
            models = []
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
            return models
        except subprocess.SubprocessError:
            return []

    def _find_fallback_model(self, exclude: Optional[str] = None) -> Optional[str]:
        installed = self._get_installed_models()
        if exclude and exclude in installed:
            installed = [m for m in installed if m != exclude]
        for fallback in self.FALLBACK_MODELS:
            if fallback in installed:
                return fallback
        return installed[0] if installed else None

    def _ollama_cli_generate(self, prompt: str, allow_retry: bool = True) -> str:
        args = ["ollama", "run", self.model, prompt]
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            return self._clean_output(result.stdout)
        except subprocess.CalledProcessError as e:
            output = self._clean_output(e.stderr or e.stdout)
            lower = output.lower()
            if allow_retry:
                fallback = self._find_fallback_model(exclude=self.model)
                if fallback and (
                    "requires more system memory" in lower
                    or "not found" in lower
                    or "not installed" in lower
                    or "unknown model" in lower
                ):
                    original = self.model
                    self.model = fallback
                    fallback_output = self._ollama_cli_generate(prompt, allow_retry=False)
                    return (
                        f"Ollama detectó que '{original}' no estaba disponible o no cabía. "
                        f"Usando '{fallback}' en su lugar.\n\n{fallback_output}"
                    )
            return f"Ollama error: {output}"
        except subprocess.TimeoutExpired:
            fallback = self._find_fallback_model(exclude=self.model)
            if allow_retry and fallback:
                original = self.model
                self.model = fallback
                fallback_output = self._ollama_cli_generate(prompt, allow_retry=False)
                return (
                    f"Ollama run agotó el tiempo con '{original}'. "
                    f"Intentando modelo ligero '{fallback}'.\n\n{fallback_output}"
                )
            return (
                "Ollama run agotó el tiempo. "
                "Asegúrate de que el modelo está instalado y que hay suficiente memoria."
            )

    def _fallback_generate(self, prompt: str) -> str:
        return f"[LLM stub] prompt length={len(prompt)}"
