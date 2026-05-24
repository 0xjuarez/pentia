# Guía de Desarrollo - Pentia v4

Para desarrolladores que quieran contribuir o entender la arquitectura interna.

## Configuración del Ambiente de Desarrollo

### 1. Clone y Setup
```bash
git clone https://github.com/tu-usuario/pentia.git
cd pentia
chmod +x install.sh
INSTALL_HEAVY=1 ./install.sh  # Instala todo incluido ML
```

### 2. Activar Entorno Virtual
```bash
source .venv/bin/activate
# o
. .venv/bin/activate
```

### 3. Verificar Setup
```bash
pentia version
pentia --help
python3 -c "import core; print('✓ Imports funcionan')"
```

### 4. Iniciar servicios auxiliares
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Tu desarrollo
source .venv/bin/activate
pentia chat  # Testea
```

## Estructura del Código

### Módulos Principales

#### `core/`
Motor principal de Pentia.

- **ai.py**: Cliente LLM con fallbacks automáticos
- **memory.py**: ChromaDB RAG y almacenamiento semántico
- **intel.py**: Inteligencia CVE (NVD, KEV, ExploitDB)
- **orchestrator.py**: Orquesta pipelines complejos
- **scoring.py**: Scoring automático de vulns
- **cve_engine.py**: Motor de búsqueda CVE
- **knowledge_graph.py**: Grafo de conocimiento
- **embeddings.py**: Proveedor de embeddings

#### `neural/`
Machine Learning.

- **classifier.py**: Clasificador de malware (XGBoost/LightGBM)
- **exploit_ranker.py**: Ranking de exploits por probabilidad
- **ioc_cluster.py**: Clustering de IoCs
- **rag.py**: RAG avanzado con reranking
- **vectorstore.py**: Gestión de bases de datos vectoriales

#### `pipelines/`
Workflows completos de ataque.

- **recon.py**: Reconocimiento DNS, Whois, Shodan, etc.
- **web.py**: Enumeration web (whatweb, ffuf, nuclei)
- **internal.py**: Scanning de redes internas (ARP, SMB, AD)
- **malware.py**: Análisis estático de PE

#### `scanners/`
Integraciones con herramientas externas.

```
scanners/
├── nmap.py          # Network scanning
├── nuclei.py        # Vulnerability scanning
├── ffuf.py          # Fuzzing web
├── subfinder.py     # Subdomain enumeration
├── whatweb.py       # Web server fingerprinting
├── web_enum.py      # Web enumeration
├── ad.py            # Active Directory
├── smb.py           # SMB enumeration
├── malware.py       # Malware samples
└── subdomains.py    # Subdomain discovery
```

#### `plugins/`
Sistema extensible.

```
plugins/
├── base.py          # Clase base para plugins
├── ffuf.py          # Wrapper ffuf
├── sqlmap.py        # Wrapper sqlmap
├── rustscan.py      # Wrapper rustscan
└── custom/          # Tus plugins personalizados
```

#### `web/`
Interfaz web.

- **app.py**: Backend FastAPI con validación de entrada
- **ui.html**: Frontend completo (HTML/CSS/JS)

#### `reports/`
Generación de reportes.

- **generator.py**: Markdown, JSON, HTML

## Flujo de Datos

```
User Input (CLI/Web)
    ↓
Validación (Pydantic/Typer)
    ↓
Pipeline (Recon/Web/Internal/Malware)
    ↓
Scanners + Orchestrator
    ↓
Core AI (LLM, Scoring, Knowledge Graph)
    ↓
Memory + RAG (ChromaDB)
    ↓
Report Generator
    ↓
Output (Console/JSON/Markdown)
```

## Patrones de Código

### Async/Await

Pentia usa asyncio para paralelización:

```python
import asyncio

async def my_scan(target: str) -> dict:
    """Escaneo asincrónico"""
    tasks = [
        scan_ports(target),
        scan_http(target),
        get_certificates(target)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {k: v for k, v in zip(["ports", "http", "certs"], results)}

# Ejecutar
asyncio.run(my_scan("example.com"))
```

### Manejo de Errores

Siempre usa try/except robusto:

```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def safe_operation(target: str) -> Optional[dict]:
    """Operación con recuperación de errores"""
    try:
        logger.debug(f"Procesando {target}")
        result = await critical_operation(target)
        logger.info(f"Éxito: {target}")
        return result
    except SpecificError as e:
        logger.warning(f"Error esperado: {e}")
        # Fallback
        return await fallback_operation(target)
    except Exception as e:
        logger.exception(f"Error inesperado en {target}: {e}")
        raise  # O retorna None/default según contexto
```

### Type Hints

Siempre usa type hints:

```python
from typing import Dict, List, Optional, Tuple
from pathlib import Path

async def process_targets(
    targets: List[str],
    timeout: int = 30,
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, any]]:
    """Procesar múltiples targets"""
    results = {}
    for target in targets:
        try:
            results[target] = await scan_target(target, timeout)
        except Exception as e:
            results[target] = {"error": str(e)}
    return results
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Mensaje de debug")           # Detalles internos
logger.info("Operación completada")        # Eventos normales
logger.warning("Config no encontrada")     # Problemas no críticos
logger.error("Failed to connect")          # Errores
logger.exception("Error inesperado")       # Con traceback
```

## Testing Local

### Testear un scanner
```bash
source .venv/bin/activate
python3 -c "
import asyncio
from scanners.nmap import scan

result = asyncio.run(scan('127.0.0.1'))
print(result)
"
```

### Testear CLI
```bash
pentia recon localhost -f
pentia web http://localhost:8000
pentia chat "¿qué es un port scan?"
```

### Testear Web API
```bash
# Terminal 1
pentia serve

# Terminal 2
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola", "model": "qwen2.5-coder"}'
```

## Performance & Optimización

### Profiling
```python
import cProfile
import pstats

pr = cProfile.Profile()
pr.enable()

# Tu código aquí
asyncio.run(my_pipeline())

pr.disable()
ps = pstats.Stats(pr)
ps.sort_stats('cumulative')
ps.print_stats(20)  # Top 20
```

### Memory
```bash
# Ver uso de memoria
/usr/bin/time -v pentia recon example.com

# O con psutil en Python
import psutil
import os
proc = psutil.Process(os.getpid())
print(f"Memory: {proc.memory_info().rss / 1024 / 1024:.2f} MB")
```

### Paralelización
```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

# CPU-bound (e.g., ML inference)
with ProcessPoolExecutor(max_workers=4) as executor:
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(executor, heavy_computation)

# I/O-bound (default)
await asyncio.gather(
    fetch_url(url1),
    fetch_url(url2),
    fetch_url(url3)
)
```

## Debugging

### Verbose Mode
```bash
PYTHONPATH=. python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from pentia import app
" serve
```

### Debugger
```python
import pdb

async def buggy_function():
    result = {}
    pdb.set_trace()  # Se detiene aquí
    return result

# o en Python 3.7+
breakpoint()  # Hace lo mismo
```

### Logs
```bash
# Ver logs en tiempo real
tail -f /tmp/pentia.log

# Buscar errors
grep ERROR /tmp/pentia.log
```

## Publicar Cambios

### Pre-commit checks
```bash
# Antes de hacer commit
python3 -m py_compile **/*.py          # Syntax
flake8 . --max-line-length=120         # Linting (si lo instalas)
```

### Commit
```bash
git add .
git commit -m "[feat]: Nueva feature que implementé"
git push origin feature-branch
```

## Recursos

- [Python asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [FastAPI docs](https://fastapi.tiangolo.com)
- [ChromaDB docs](https://docs.trychroma.com)
- [Ollama docs](https://github.com/ollama/ollama)
- [Typer docs](https://typer.tiangolo.com)
- [Rich docs](https://rich.readthedocs.io)

## Preguntas?

Abre un Issue con etiqueta `question` o revisa el código existente.

---

Happy hacking! 🚀
