# Pentia v4

```
██████╗  ███████╗███╗   ██╗████████╗██╗  █████╗
██╔══██╗██╔════╝████╗  ██║╚══██╔══╝██║ ██╔══██╗
██████╔╝█████╗  ██╔██╗ ██║   ██║   ██║ ███████║
██╔═══╝ ██╔══╝  ██║╚██╗██║   ██║   ██║ ██╔══██║
██║     ███████╗██║ ╚████║   ██║   ██║ ██║  ██║
╚═╝     ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═╝ ╚═╝
v4 · Red Team AI Platform
```

PENTIA es una herramienta de línea de comandos con interfaz web para
pruebas de seguridad autorizadas: reconocimiento, enumeración web e
interna, análisis de malware, enriquecimiento de CVE y chat local con
un modelo de lenguaje a través de Ollama. Está pensada para usarse
contra sistemas propios o con autorización explícita por escrito.

**4.0.3 (2026-11-10).** Instalador automático (`./install.sh --all`:
base + herramientas + ML + Ollama + modelo + verificación) y
corrección del comando `pentia`, que fallaba al arrancar por la ruta
del wrapper. Cada paso limpia la pantalla y la salida de `pip` es
silenciosa. Detalle completo en [CHANGELOG.md](CHANGELOG.md).

**4.0.2 (2026-11-10).** Esta versión reescribe el README sin adornos,
añade un canal concreto para reportar vulnerabilidades (ver
[SECURITY.md](SECURITY.md)), adapta el instalador a varias
distribuciones, cambia el modelo de lenguaje por defecto a uno ligero
(`qwen2.5-coder:1.5b`) y evita que los despliegues con varios commits
disparen ejecuciones de CI obsoletas. Detalle completo en
[CHANGELOG.md](CHANGELOG.md).

**4.0.1 (2026-11-10).** Revisión de seguridad y hardening: validación
de targets, timeouts y verificación de binarios en los scanners, CORS
y localhost-only en la Web UI, XSS escapado en la UI y en los
reportes, parseo NVD 2.0 y suite de tests (`pytest tests/`).

## Alcance

PENTIA es un proyecto personal en desarrollo activo, no un producto
terminado. Espera errores y comportamiento incompleto en algunas
partes. Úsalo solo contra sistemas que te pertenecen o que tienes
autorización explícita para probar. No lo uses contra sistemas de
terceros ni para acceder, interrumpir o extraer datos sin permiso.

La interfaz web (`pentia serve`) **no tiene autenticación por
diseño**: escucha solo en `127.0.0.1` y rechaza cualquier cliente que
no sea local. No la expongas en red local ni en internet. Lee
[SECURITY.md](SECURITY.md) antes de usarla.

## Requisitos

Instalación base (ligera, sin modelos pesados):

| Recurso | Requisito |
|---------|-----------|
| Python | 3.11 o superior |
| RAM | 2 GB |
| CPU | 2 núcleos |
| Disco | 500 MB libres |

La instalación base no incluye los módulos de aprendizaje automático
ni memoria semántica (RAG). Esos son opcionales (`INSTALL_HEAVY=1`):
descargan varios cientos de MB en paquetes (ChromaDB,
sentence-transformers, XGBoost, LightGBM, scikit-learn, networkx,
pefile) más el modelo de embeddings, y necesitan compiladores C++
(`build-essential` o equivalente) porque algunos paquetes se compilan
al instalarse. En equipos modestos la instalación pesada tarda
bastante; si solo vas a hacer recon y enriquecimiento de CVE, no la
necesitas.

Las herramientas externas de escaneo (nmap, nuclei, ffuf, subfinder,
whatweb, sqlmap, rustscan, wpscan) no se instalan con la instalación
base. PENTIA avisa cuáles faltan y sigue funcionando con las que hay.
Para instalarlas, usa `INSTALL_TOOLS=1 ./install.sh` (ver abajo).

## Instalación

### Instalación automática (recomendado)

Un solo comando hace todo: base, herramientas del sistema, funciones
de ML y memoria, Ollama, el modelo ligero y la verificación final.

```bash
git clone https://github.com/0xjuarez/pentia.git pentia
cd pentia
./install.sh --all
```

Con `--all` el instalador pregunta antes de cada paso que usa `sudo`
o descarga algo (Ollama). Para que no pregunte nada, agrega `--yes`:

```bash
./install.sh --all --yes
```

Al final verifica que el comando `pentia` arranca de verdad
(`pentia version` y `pentia --help`); si el wrapper falla, la
instalación se detiene con error en vez de dejar un comando roto.
Cada paso limpia la pantalla, así que se ve solo el proceso en curso.

### Instalación manual, por partes

Si prefieres instalar solo lo que necesitas:

```bash
git clone https://github.com/0xjuarez/pentia.git pentia
cd pentia
chmod +x install.sh
```

#### 1. Base

```bash
./install.sh
```

Crea el entorno virtual `.venv`, instala las dependencias base
desde `requirements.txt` y deja el comando `pentia` disponible en
`~/.local/bin`. Detecta la distribución desde `/etc/os-release`
(Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE, Alpine y macOS con
Homebrew) para darte los comandos correctos si falta `pip` o
`python3-venv`. No descarga ni ejecuta instaladores remotos.

#### 2. Herramientas de escaneo del sistema (opcional)

```bash
INSTALL_TOOLS=1 ./install.sh
```

Instala con el gestor de paquetes de tu distribución las
herramientas que estén en sus repositorios (nmap, ffuf, sqlmap,
whatweb y, según la distro, otras). Antes de usar `sudo` te pregunta
y solo continúa si confirmas. nuclei, subfinder, rustscan y wpscan no
están en la mayoría de los repositorios; instálalos a mano:

```bash
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
cargo install rustscan
gem install wpscan
```

#### 3. Funciones de ML y memoria (opcional)

```bash
INSTALL_HEAVY=1 ./install.sh
```

Instala los paquetes de aprendizaje automático uno por uno: si uno
falla, avisa y sigue con el resto en lugar de abortar todo.

#### 4. Chat local con Ollama (opcional, solo para `pentia chat`)

```bash
# Instala Ollama desde https://ollama.com/download y luego:
ollama pull qwen2.5-coder:1.5b
```

El modelo por defecto es `qwen2.5-coder:1.5b` (alrededor de 1 GB),
elegido para que corra en equipos comunes. Puedes usar otro modelo
con `OLLAMA_MODEL` o con `pentia chat --model <nombre>`.

#### 5. Verificar la instalación

```bash
pentia version
pentia --help
```

Si aparece `pentia: command not found`, recarga tu shell:

```bash
source ~/.bashrc  # o source ~/.zshrc
```

## Uso

### Interfaz web

```bash
pentia serve
# Abre http://127.0.0.1:8000
```

Opciones: `--host` (por defecto `127.0.0.1`) y `--port` (por
defecto `8000`). Mantén el host en `127.0.0.1`: la interfaz no tiene
login y cualquiera que la alcance puede lanzar escaneos y usar el
modelo local.

### Menú principal

```bash
pentia                    # Menú principal
pentia --help             # Todos los comandos
pentia version            # Información de versión
```

### Comandos

```bash
# Recon y escaneo
pentia recon example.com           # Pipeline completo: nmap, nuclei, subfinder, ffuf, CVE
pentia recon example.com -f        # Modo rápido (sin ffuf)
pentia recon example.com -o reports
pentia web example.com             # Enumeración web: whatweb, ffuf
pentia internal 192.168.1.0/24     # Red interna: enum4linux, Bloodhound

# Inteligencia de CVE
pentia cve scanme.nmap.org Apache 2.4.49   # Enriquecimiento: CPE, NVD, KEV, ExploitDB, nuclei
pentia intel "apache path traversal"       # Búsqueda en inteligencia local
pentia intel-download --kev                # Descargar feeds CISA KEV y/o NVD
pentia ingest-intel datasets/cves/nvdcve.json   # Ingerir un archivo NVD JSON o ExploitDB CSV

# Memoria y chat
pentia memory "apache exploit"     # Búsqueda en memoria semántica (ChromaDB local)
pentia chat                        # Chat interactivo (requiere Ollama)
pentia chat --model llama3.1       # Otro modelo Ollama

# Malware y reportes
pentia malware /ruta/muestra.exe   # Análisis: features PE, entropía, clasificación
pentia report "hallazgos" -o reports   # Reporte en Markdown y JSON
```

Los reportes se guardan en el directorio de trabajo actual. Los
nombres de archivo derivados del target se sanean para evitar
escrituras fuera del directorio de salida.

## Capturas de pantalla

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

## Estructura

```
pentia/
├── pentia.py              # CLI principal (Typer + Rich)
├── install.sh             # Instalador
├── requirements.txt        # Dependencias base
├── pyproject.toml          # Configuración Python
│
├── web/
│   ├── app.py             # Backend FastAPI
│   └── ui.html            # Frontend
│
├── core/                   # Motor principal
│   ├── ai.py              # Cliente LLM (Ollama)
│   ├── memory.py          # RAG y ChromaDB
│   ├── intel.py           # Enriquecimiento CVE
│   ├── orchestrator.py    # Orquestación de pipelines
│   ├── scoring.py         # Scoring de findings
│   ├── cve_engine.py      # Motor CVE
│   ├── knowledge_graph.py  # Grafo de conocimiento
│   ├── validation.py      # Validación de targets y modelos
│   └── ... (otros módulos)
│
├── neural/                 # Aprendizaje automático (opcional)
│   ├── classifier.py      # Clasificador de malware
│   ├── exploit_ranker.py  # Ranking de exploits
│   ├── ioc_cluster.py     # Clustering de IOCs
│   ├── rag.py             # RAG avanzado
│   └── vectorstore.py     # Gestión de embeddings
│
├── pipelines/             # Pipelines de recon, web, internal, malware
├── scanners/              # Integraciones con binarios externos
├── plugins/               # Sistema modular (ffuf, sqlmap, rustscan)
├── reports/               # Generación de reportes (Markdown, JSON, HTML)
├── scripts/               # Descarga de inteligencia (KEV, NVD)
└── tests/                 # Suite de tests (pytest)
```

## Configuración

Variables de entorno (ver `.env.example`, copia a `.env`):

```bash
# Modelo de lenguaje (Ollama)
OLLAMA_MODEL="qwen2.5-coder:1.5b"  # Modelo por defecto
OLLAMA_HOST="http://localhost:11434"

# Escaneo
NUCLEI_TEMPLATES="/usr/share/nuclei-templates"
SHODAN_API_KEY="your-key"

# Web
WEB_PORT=8000
WEB_HOST=127.0.0.1
```

Para activar el entorno virtual manualmente:

```bash
source .venv/bin/activate
# Desactivar
deactivate
```

## Desarrollar y contribuir

Este es un proyecto personal, pero las contribuciones son
bienvenidas. Antes de enviar cambios, corre la suite de tests:

```bash
pytest tests/ -q
```

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

## Solución de problemas

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

# Descarga el modelo por defecto si falta
ollama pull qwen2.5-coder:1.5b
```

### Errores de dependencias ML

```bash
# Instala compiladores (Debian/Ubuntu):
sudo apt-get install build-essential python3-dev

# Fedora/RHEL:
sudo dnf install gcc gcc-c++ python3-devel

# macOS:
xcode-select --install

# Luego reintenta
INSTALL_HEAVY=1 ./install.sh
```

Más casos en [TROUBLESHOOTING.md](TROUBLESHOOTING.md) y
[DEVELOPMENT.md](DEVELOPMENT.md).

## Licencia

Este es un proyecto personal sin licencia específica.
Siéntete libre de modificar, adaptar y redistribuir según tus
necesidades.

## Soporte

- **Bugs**: Abre un issue con detalles de reproducción
- **Vulnerabilidades**: No las publiques; repórtalas por correo
  según [SECURITY.md](SECURITY.md)
- **Preguntas**: Revisa la documentación primero

---

**Última actualización**: 10 de noviembre de 2026
**Versión**: 4.0.3
