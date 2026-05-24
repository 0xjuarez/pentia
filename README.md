# Pentia v4 — Red Team AI Platform

```
██████╗  ███████╗███╗   ██╗████████╗██╗  █████╗
██╔══██╗██╔════╝████╗  ██║╚══██╔══╝██║ ██╔══██╗
██████╔╝█████╗  ██╔██╗ ██║   ██║   ██║ ███████║
██╔═══╝ ██╔══╝  ██║╚██╗██║   ██║   ██║ ██╔══██║
██║     ███████╗██║ ╚████║   ██║   ██║ ██║  ██║
╚═╝     ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═╝  ╚═╝
v4 · Red Team AI Platform
```

## ⚠️ Información Importante

> **Este es un proyecto personal en desarrollo activo.** No está optimizado para uso en producción ni uso diario.
>
> - 🔧 **Estado**: Versión experimental. Espera bugs y comportamientos inesperados
> - 🚀 **Desarrollo**: El proyecto continúa evolucionando. Nuevas features y fixes se agregan regularmente
> - 📦 **Recursos**: Requiere recursos significativos para óptimo rendimiento
> - ✏️ **Personalización**: Siéntete libre de modificar el código según tus necesidades
>
> **No esperes que funcione perfectamente a la primera.** Si encuentras issues, por favor reportalos.

### Requisitos Mínimos Recomendados

Para un rendimiento aceptable, tu sistema debe tener:

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| **RAM** | 8 GB | 16 GB+ |
| **CPU** | 4 cores | 8+ cores (con paralelización) |
| **Almacenamiento** | 20 GB | 100 GB+ (para inteligencia, modelos) |
| **Python** | 3.11 | 3.12+ |

Si planeas usar **características ML/AI completas** (clasificación, RAG, embeddings), necesitarás especialmente:
- **32 GB+ RAM** (para modelos grandes)
- **SSD rápido** (para bases de datos vectoriales)
- **GPU opcional** (acelera significativamente ML)

---

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

```bash
https://github.com/0xjuarez/pentia.git pentia
cd pentia
chmod +x install.sh
```

### 2. Instalar (instalación base)

```bash
./install.sh
```

Esto instalará:
- ✓ Entorno virtual Python 3.11+
- ✓ Dependencias CLI (Typer, Rich, FastAPI)
- ✓ Herramientas de recon básicas

### 3. Instalar con ML/AI completo (opcional)

```bash
INSTALL_HEAVY=1 ./install.sh
```

Agrega:
- ChromaDB (para RAG/Memoria)
- Transformers (embeddings)
- XGBoost, LightGBM (clasificación)
- FAISS (búsqueda vectorial)

**Nota**: Esto tarda más y requiere compiladores C++ disponibles.

### 4. (Requerido para chat) Instalar Ollama

Para usar el chat AI integrado:

```bash
# Descargar desde https://ollama.com/download
ollama pull qwen2.5-coder  # o tu modelo favorito
```

### 5. Verificar instalación

```bash
pentia version
pentia --help
```

Si `pentia: command not found`, reinicia tu shell:
```bash
source ~/.bashrc  # o source ~/.zshrc
```

---

## 📋 Uso Rápido

### Interfaz Web (Recomendada)

```bash
pentia serve
# Abre http://127.0.0.1:8000
```

### Terminal Interactiva

```bash
pentia                    # Menú principal
pentia --help             # Todos los comandos
pentia version            # Info del sistema
```

### Comandos Principales

```bash
# ── Recon y Scanning ──
pentia recon example.com           # Pipeline completo
pentia recon example.com -f        # Modo rápido (sin nuclei)
pentia web example.com             # Web enumeration
pentia internal 192.168.1.0/24     # Scanning interno

# ── Inteligencia CVE ──
pentia cve scanme.nmap.org Apache 2.4.49     # Enriquecimiento
pentia intel "apache path traversal"          # Búsqueda
pentia intel-download --kev                   # Descargar KEV
pentia ingest-intel datasets/cves/nvdcve.json # Ingerir datos

# ── AI Chat ──
pentia chat                    # Chat interactivo
pentia chat --model llama3.1   # Otro modelo Ollama

# ── Memoria & RAG ──
pentia memory "apache exploit" # Búsqueda en memoria

# ── Malware ──
pentia malware /path/sample.exe  # Análisis

# ── Reportes ──
pentia report "findings" -o ./reports/
```

---

## 📸 Capturas de Pantalla

### Web UI
![Web Interface 1](assets/Captura%20desde%202026-05-23%2019-12-09.png)
*Interfaz principal*

![Web Interface 2](assets/Captura%20desde%202026-05-23%2019-51-27.png)
*Panel de análisis*

![Web Interface 3](assets/Captura%20desde%202026-05-23%2019-51-32.png)
*Resultados de recon*

![Web Interface 4](assets/Captura%20desde%202026-05-23%2019-51-36.png)
*Inteligencia CVE*

![Web Interface 5](assets/Captura%20desde%202026-05-23%2019-51-40.png)
*Chat AI integrado*

---

## 🏗️ Arquitectura

```
pentia/
├── pentia.py              # CLI principal (Typer + Rich)
├── install.sh             # Instalador inteligente
├── requirements.txt        # Dependencias
├── pyproject.toml          # Configuración Python
│
├── web/
│   ├── app.py             # Backend FastAPI
│   └── ui.html            # Frontend completo
│
├── core/                   # Motor principal
│   ├── ai.py              # Cliente LLM (Ollama)
│   ├── memory.py          # RAG & ChromaDB
│   ├── intel.py           # Enriquecimiento CVE
│   ├── orchestrator.py    # Orquestación de pipelines
│   ├── scoring.py         # Scoring automático
│   ├── cve_engine.py      # Motor CVE
│   ├── knowledge_graph.py  # Grafo de conocimiento
│   └── ... (otros módulos)
│
├── neural/                 # Machine Learning
│   ├── classifier.py      # Clasificador malware
│   ├── exploit_ranker.py  # Ranking de exploits
│   ├── ioc_cluster.py     # Clustering de IOCs
│   ├── rag.py             # RAG avanzado
│   └── vectorstore.py     # Gestión de embeddings
│
├── pipelines/             # Pipelines de ataque
│   ├── recon.py           # Reconocimiento
│   ├── web.py             # Web testing
│   ├── internal.py        # Red interna
│   └── malware.py         # Análisis malware
│
├── scanners/              # Integraciones
│   ├── nmap.py, nuclei.py, whatweb.py
│   ├── subdomains.py, web_enum.py
│   └── ... (más herramientas)
│
├── plugins/               # Sistema modular
│   ├── base.py            # Plugin base
│   ├── ffuf.py, sqlmap.py, rustscan.py
│   └── custom/            # Tus propios plugins
│
├── reports/               # Generación
│   └── generator.py       # Markdown + JSON
│
└── scripts/
    └── download_intel.py  # Descarga de inteligencia
```

---

## ⚙️ Configuración

### Variables de Entorno

```bash
# Modelos
OLLAMA_MODEL="qwen2.5-coder"  # Modelo por defecto
OLLAMA_HOST="http://localhost:11434"

# Scanning
NUCLEI_TEMPLATES="/path/to/templates"
SHODAN_API_KEY="your-key"

# Web
WEB_PORT=8000
WEB_HOST=127.0.0.1
```

### Activar manualmente el entorno

```bash
source .venv/bin/activate
# o
. .venv/bin/activate

# Desactivar
deactivate
```

---

## 🔧 Desarrollar & Contribuir

Este es un proyecto personal, pero **todas las contribuciones son bienvenidas**.

### Estructura de código

- **Modular**: Cada scanner/pipeline es independiente
- **Async-first**: Usa `asyncio` para paralelización
- **Tipado**: Type hints en todo el código
- **Errores manejados**: Recuperación automática de fallos

### Agregar un scanner personalizado

```python
# plugins/custom/mi_scanner.py
from plugins.base import ScannerBase

class MiScanner(ScannerBase):
    def __init__(self):
        super().__init__(name="mi_scanner", version="1.0")
    
    async def scan(self, target: str):
        # Tu lógica aquí
        return results
```

---

## 🐛 Troubleshooting

### "pentia: command not found"

```bash
# Verifica que ~/.local/bin está en PATH
echo $PATH

# Si no, agrega a tu shell rc (~/.bashrc, ~/.zshrc):
export PATH="$HOME/.local/bin:$PATH"

# Luego recarga
source ~/.bashrc
```

### "No se pudo activar .venv"

```bash
# Reinstala el entorno
cd /ruta/pentia
rm -rf .venv
./install.sh
```

### "Ollama no conecta"

```bash
# Verifica que Ollama está corriendo
ollama serve  # En otra terminal

# Verifica el modelo
ollama list

# Descarga si falta
ollama pull qwen2.5-coder
```

### Errores de dependencias ML/AI

```bash
# Si falla INSTALL_HEAVY=1, instala compiladores
# Ubuntu/Debian:
sudo apt-get install build-essential python3-dev

# macOS:
xcode-select --install

# Luego reintenta
INSTALL_HEAVY=1 ./install.sh
```

---

## 📄 Licencia

Este es un proyecto personal sin licencia específica.  
**Siéntete libre de modificar, adaptar y redistributir según tus necesidades.**

---

## 🤝 Soporte

- **Bugs**: Abre un issue con detalles de reproducción
- **Features**: Sugiere en issues
- **Preguntas**: Revisa la documentación primero

---

**Última actualización**: Mayo 2026  
**Versión**: 4.0.0 (En desarrollo)
