# Changelog - Pentia v4

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [4.0.2] - 2026-11-10 — Documentación, instalador multi-distro y modelo ligero

Sin cambios de funcionalidad de escaneo: esta versión es
documentación, instalador y ajustes para equipos comunes.

### Documentación
- README reescrito por completo en español, sin emojis ni lenguaje
  de marketing: qué es PENTIA, alcance honesto (proyecto personal,
  uso autorizado únicamente), requisitos reales de la instalación
  base (Python 3.11+, 2 GB RAM, 2 núcleos, 500 MB de disco), costo
  real de la instalación pesada opcional, comandos verificados contra
  `pentia --help` y advertencia de que la Web UI no tiene
  autenticación por diseño (solo localhost).
- `SECURITY.md`: canal concreto para reportar vulnerabilidades —
  correo jesjuarez590@gmail.com con asunto "Vulnerabilidad en
  PENTIA", incluyendo versión afectada, pasos para reproducir e
  impacto; sin publicar la vulnerabilidad, PoC ni detalles de
  explotación antes de que haya una corrección.

### Instalador
- `install.sh` detecta la distribución desde `/etc/os-release`
  (Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE, Alpine, macOS con
  Homebrew) y usa su gestor de paquetes. Corrige el consejo
  erróneo "Debian/Ubuntu/Fedora: sudo apt install python3-pip"
  (Fedora usa dnf, no apt).
- Detección fail-fast de `python3-venv` (Debian/Ubuntu lo separan
  en otro paquete): si falta, el instalador se detiene con el
  comando exacto para instalarlo en lugar de fallar a mitad de la
  creación del entorno virtual.
- Instalación opcional de herramientas del sistema detrás de
  `INSTALL_TOOLS=1` (nmap, ffuf, sqlmap, whatweb y, según la
  distro, otras): pregunta antes de usar sudo y nunca lo usa sin
  confirmación. nuclei, subfinder, rustscan y wpscan no están en la
  mayoría de los repositorios y se documentan con sus comandos de
  instalación manual en el README.
- La instalación pesada (`INSTALL_HEAVY=1`) instala los paquetes
  ML uno por uno: si uno falla, avisa y sigue con el resto en lugar
  de abortar todo.

### Modelo por defecto
- El modelo de lenguaje por defecto pasa de `qwen2.5-coder` (7B,
  ~4.7 GB) a `qwen2.5-coder:1.5b` (~1 GB) en `core/ai.py`,
  `pentia chat --model`, la API web (`/api/chat`), `.env.example`,
  `install.sh` y la documentación, para que corra en equipos
  comunes. `OLLAMA_MODEL` sigue permitiendo elegir otro modelo y
  los fallbacks siguen siendo modelos pequeños primero.

### CI
- `.github/workflows/python-tests.yml`: grupo de concurrencia por
  workflow y rama con `cancel-in-progress: true`, para que un push
  con varios commits cancele las ejecuciones intermedias en lugar
  de producir fallos y correos por estados transitorios.

## [4.0.1] - 2026-11-10 — Revisión de seguridad y hardening

Auditoría completa (seguridad, web UI, dependencias, CLI/lógica) y
corrección de lo encontrado. Sin módulos de exploit nuevos: solo hardening.

### 🔒 Seguridad
- Validación de targets en toda entrada (CLI y web): nuevo `core/validation.py`
  (`validate_target`, `validate_url`, `validate_model_name`,
  `validate_output_dir`, `sanitize_filename`). Rechaza targets que empiezan
  con `-`, metacaracteres de shell (`; & | $ \``), espacios y URLs con
  credenciales o esquema no http(s). Los scanners ya no reciben un target
  sin validar como argumento posicional.
- Nuevo `scanners/_common.py::run_tool`: todos los scanners/plugins usan
  listas de argumentos (sin shell), con `--` antes del target donde el
  binario lo soporta, verificación de binario con `shutil.which`, timeout
  (120 s por defecto, `asyncio.wait_for` + kill) y límite de salida de
  1 MB. Sin timeouts infinitos en `communicate()`.
- Web UI: CORS limitado a `http://127.0.0.1:8000` y `http://localhost:8000`
  con `allow_credentials=False`; middleware localhost-only (403 a cualquier
  cliente no loopback); cabeceras CSP, `X-Frame-Options: DENY` y
  `X-Content-Type-Options: nosniff`; validadores pydantic v2
  (`@field_validator`, adiós `@validator` deprecado); los errores 500 ya no
  filtran detalles de excepciones (se registran en log); el modelo de chat
  se valida con allowlist antes de llegar a `ollama run`.
- Web UI: `ui.html` escapa con `esc()` todo dato dinámico antes de
  `innerHTML` (resultados CVE/recon/memoria y errores) — ya no hay XSS
  almacenado desde banners o entradas NVD/memoria.
- `scripts/download_intel.py`: `--nvd-url` solo acepta hosts NVD/CISA
  (allowlist), descarga por streaming con tope de 500 MB, escribe bytes
  (antes `write_text` corrompía los `.gz`) y valida `--out`.
- `install.sh`: eliminado `curl …/get-pip.py | python3 -`; ahora instala
  desde `requirements.txt` (versiones acotadas) y ya no oculta errores de
  pip con `2>/dev/null`; el fallo de la instalación pesada ya no imprime
  un falso `ok "ML/AI instalado"`.
- Reportes: `write_reports` usa `json.dumps` (el `report.json` de 4.0.0 era
  `str(dict)`, JSON inválido), escapa HTML con `html.escape` y escribe de
  forma atómica; el directorio de salida queda confinado al CWD.
- Caché: `CACHE_DIR` ya no es `/home/venus/ai/pentia/cache`; se configura
  con `PENTIA_CACHE_DIR` o `~/.pentia/cache`, con escrituras atómicas y
  nombres de archivo saneados (sin path traversal por target).
- `pentia serve` ahora lee `WEB_HOST`/`WEB_PORT` del entorno (antes estaban
  documentadas en el README pero ningún código las leía) y avisa si el host
  no es loopback: la UI no tiene autenticación por diseño.

### 🐛 Arreglado
- `core/ai.py`: las 6 funciones duplicadas (`_clean_output`,
  `_ollama_generate`, `_ollama_model_available`, `_find_fallback_model`,
  `_ollama_cli_generate`, `_fallback_generate`) quedan en una sola
  definición cada una; `generate()` ya no muta `self.model` al fallback.
- CVE: `core/cve_engine.py` y `core/cve_intelligence.py` parsean el esquema
  NVD 2.0 primero (1.x como fallback); `ingest_nvd_file` acepta
  `vulnerabilities` y `CVE_Items`; `ingest_exploitdb_file` parsea CSV con
  comas (antes partía por tabulador y siempre ingería 0 registros);
  `resultsPerPage=2000` en la búsqueda NVD.
- `pentia malware` leía `results["features"]`/`["prediction"]` pero el
  pipeline devuelve `static_analysis`/`classification`: ahora muestra
  etiqueta y confianza reales en vez de `unknown / 0%`.
- `pentia recon -o` llamaba a `_recon_summary`/`_recon_findings` sin
  definirlos (NameError): helpers añadidos; el reporte ya no es
  `str(results)`. `orchestrator.route()` ya no vuelve a correr nuclei/ffuf
  (skip) y corre sus scanners en paralelo con `gather`.
- `core/memory.py`: eliminado el ajuste deprecado
  `chroma_db_impl="duckdb+parquet"`; `MemoryStore` usa `PersistentClient`;
  `recon`/`memory`/`intel`/`chat` ya no se caen si falta ChromaDB (avisan
  y siguen). `core/knowledge_graph.py`: el fallback sin networkx ya no
  mete un dict en un set (`TypeError`).
- `core/cpe.py` construye CPE sin versión (`*`); `core/decision_engine.py`
  añade regla `ldap → enum4linux` y corrige el falso positivo `"wp" in s`.
- `core/scoring.py`: un solo `ExploitRanker` por proceso y el factor de
  exploit se cuenta una vez; un CVSS 10 sin PoC público ya no puntúa 0.0.
- `neural/exploit_ranker.py::fit()` persistía solo un JSON de parámetros
  (entrenamiento perdido): ahora guarda el modelo con pickle (solo archivos
  locales de confianza, ver `SECURITY.md`).
- `neural/classifier.py`: `entropy()` con `Counter` (una pasada),
  `features["size"]` es el tamaño real del archivo, `fit()` no se rompe
  con un `Booster` de LightGBM. `neural/ioc_cluster.py` no se rompe con
  lista vacía. `neural/code_analyzer.py` y `core/embeddings.py` cargan el
  modelo de forma perezosa (antes descargaban en `__init__`).
- `scanners/nmap.py`: eliminado el `run_nuclei` duplicado (con `-t -`
  roto); `plugins/rustscan.py` pasa `-a <target>` (antes fallaba sin `-a`);
  `scanners/ad.py::run_bloodhound` ya no invoca un binario `bloodhound`
  inexistente (devuelve error claro); `scanners/malware.py` captura
  `PEFormatError` en no-PE; `scanners/web_enum.py::run_subfinder` delega
  en `scanners/subdomains.py`.
- `core/intel.py`: KEV con caché TTL 1 h y lookup O(1) por set; los
  índices ExploitDB/Nuclei se construyen una vez por llamada; los fallos
  de KEV/NVD ahora se registran con warning en vez de silenciarse.
- `core/cache.py`: `load_nvd_cache` tolera JSON corrupto (devuelve `{}`).
- `pentia.py`: el `def main` duplicado queda como callback `main` +
  entrada `run_cli`; `intel-download` resuelve el script respecto al
  proyecto (no al CWD) y con timeout 600 s; `_print_results_table` marca
  ✗ los `returncode != 0`; el `chat /memory` no mata la sesión si falla
  ChromaDB; `report` avisa si el JSON no parsea; entradas de usuario
  escapadas con `rich.markup.escape()` en la salida Rich.
- `pyproject.toml`: backend de build roto
  (`setuptools.backends.legacy:build` no existe) → `setuptools.build_meta`,
  con descubrimiento explícito de paquetes y `web/*.html` como
  package-data, por lo que `pip install .` vuelve a funcionar.
  `scripts/__init__.py` añadido para que `pip install` incluya el
  downloader de intel.
- Dependencias core con rangos acotados (`typer[all]>=0.12,<0.21`,
  `rich>=13.7,<15`, `httpx>=0.27,<0.29`, `requests>=2.32,<2.33`,
  `fastapi>=0.115,<0.130`, `uvicorn>=0.30,<0.38`, `pydantic>=2.9,<3`);
  `faiss-cpu` y `torch` eliminados (nada los importa); cliente `ollama`
  documentado como opcional. `.env.example`: `CHROMADB_PORT` 8000 → 8001
  (chocaba con `WEB_PORT`).
- README: snippet de instalación corregido (`git clone …`),
  modo rápido documentado como "sin ffuf" (no "sin nuclei"),
  docstring de `pentia web` corregido a `whatweb → ffuf` y el de
  `internal` a `enum4linux → Bloodhound`. `Modelfile` dice v4 (era v3).
  CI: `py_compile` ahora cubre subdirectorios, acciones actualizadas
  (checkout v4, setup-python v5), matriz Python 3.11/3.12, y el job de
  tests ejecuta `pytest tests/ -q` y ya no traga errores.
- Nuevo `SECURITY.md` (uso autorizado, cómo reportar, UI localhost-only,
  modelos solo de fuentes confiables) y suite de tests `tests/` (83 tests:
  validación, reportes, parseo NVD, caché, `run_tool`, CLI, web UI).

### ⚠️ Por Hacer (Roadmap)
- [x] Tests unitarios y de integración
- [ ] Caché persistente para resultados
- [ ] WebSockets para actualizaciones en tiempo real
- [ ] Autenticación en Web UI
- [ ] API autenticada
- [ ] Dashboard de estadísticas
- [x] Export a formatos adicionales (HTML, PDF) — export HTML añadido
- [ ] Paralelización mejorada
- [ ] GPU acceleration para ML
- [ ] Integración con más herramientas

## [4.0.0] - Mayo 2026

### ✨ Nuevas Features
- CLI completa con Typer
- Web UI con FastAPI
- Integración con Ollama para chat AI
- RAG con ChromaDB y Memoria semántica
- Inteligencia CVE (NVD + KEV + ExploitDB)
- Pipelines de recon, web, internal, malware
- Clasificación neural de malware
- Scoring automático de findings
- Generador de reportes (MD/JSON)
- Sistema de plugins modular

### 🔧 Mejorado
- Manejo robusto de errores
- Fallbacks automáticos para Ollama
- Validación de entrada en web API
- Logging estructurado
- Instalador mejorado con verificaciones

### 🐛 Arreglado
- Activación de .venv en install.sh
- Manejo de módulos faltantes
- Error messages más claros

### 📦 Dependencias
- Python 3.11+
- Ollama (opcional, para chat)
- Herramientas: nmap, nuclei, ffuf, etc. (opcional)
- ML: chromadb, transformers, xgboost (opcional)

---

## Versiones Anteriores

- **v3.x**: Arquitectura anterior (deprecada)
- **v2.x**: Primera generación (archived)
