#!/usr/bin/env bash
# ============================================================
#  PENTIA v4 — Red Team AI Platform  |  install.sh
#  DevSecurityMX · Jesús Juárez
# ============================================================
set -euo pipefail

# Colores con $'...' (ANSI-C): la variable ya contiene el byte ESC real.
# Con '\033[...' entre comillas simples, printf solo interpreta el
# escape en la cadena de formato, y dentro de los mensajes (%s) el
# código se imprimía literalmente ("\033[0;36m...").
RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YLW=$'\033[1;33m'
CYN=$'\033[0;36m'; WHT=$'\033[1;37m'; MGN=$'\033[0;35m'
BLU=$'\033[0;34m'; DIM=$'\033[2m'; BLD=$'\033[1m'; NC=$'\033[0m'

print_banner() {
  printf "\n"
  printf "${RED}██████╗ ${YLW} ███████╗${GRN}███╗   ██╗${CYN}████████╗${BLU}██╗ ${MGN} █████╗ ${NC}\n"
  printf "${RED}██╔══██╗${YLW}██╔════╝${GRN}████╗  ██║${CYN}╚══██╔══╝${BLU}██║${MGN}██╔══██╗${NC}\n"
  printf "${RED}██████╔╝${YLW}█████╗  ${GRN}██╔██╗ ██║${CYN}   ██║   ${BLU}██║${MGN}███████║${NC}\n"
  printf "${RED}██╔═══╝ ${YLW}██╔══╝  ${GRN}██║╚██╗██║${CYN}   ██║   ${BLU}██║${MGN}██╔══██║${NC}\n"
  printf "${RED}██║     ${YLW}███████╗${GRN}██║ ╚████║${CYN}   ██║   ${BLU}██║${MGN}██║  ██║${NC}\n"
  printf "${RED}╚═╝     ${YLW}╚══════╝${GRN}╚═╝  ╚═══╝${CYN}   ╚═╝   ${BLU}╚═╝${MGN}╚═╝  ╚═╝${NC}\n"
  printf "\n"
  printf "  ${WHT}v4${NC} ${DIM}·${NC} ${GRN}Red Team AI Platform${NC} ${DIM}·${NC} ${CYN}DevSecurityMX${NC}\n"
  printf "  ${DIM}Jesús Juárez · Red Team Senior${NC}\n"
  printf "\n"
  printf "  ${DIM}────────────────────────────────────────────────────${NC}\n\n"
}

ok()   { printf "  ${GRN}✓${NC}  %s\n" "$*"; }
fail() { printf "  ${RED}✗${NC}  %s\n" "$*"; }
info() { printf "  ${CYN}→${NC}  %s\n" "$*"; }
warn() { printf "  ${YLW}⚠${NC}  %s\n" "$*"; }
line() { printf "  ${DIM}────────────────────────────────────────────${NC}\n"; }

# Limpia la pantalla antes de cada paso (solo si hay terminal: con la
# salida redirigida o en CI no hace nada, para no ensuciar los logs).
clear_screen() {
  if [ -t 1 ]; then
    clear 2>/dev/null || true
  fi
}

# Cada paso limpia la pantalla: se ve solo el proceso en curso.
step() {
  clear_screen
  printf "  ${BLD}${WHT}[$1]${NC} ${WHT}$2${NC}\n"
}

OLLAMA_OK=false

# Flags: --all instala todo (herramientas + ML pesado + Ollama + modelo
# + verificación) y --yes/-y confirma las preguntas automáticamente.
# Sin flags, el comportamiento es el de siempre (solo base, con preguntas).
AUTO_YES=false
INSTALL_OLLAMA=0

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --all)
        INSTALL_TOOLS=1
        INSTALL_HEAVY=1
        INSTALL_OLLAMA=1
        ;;
      --yes|-y)
        AUTO_YES=true
        ;;
      --help|-h)
        printf "Uso: ./install.sh [--all] [--yes]\n\n"
        printf "  (sin flags)  Solo instalación base (venv + dependencias core + comando pentia).\n"
        printf "  --all        Todo: base + herramientas del sistema + ML pesado + Ollama\n"
        printf "               + modelo qwen2.5-coder:1.5b + verificación final.\n"
        printf "  --yes, -y    Confirma automáticamente las preguntas (sudo, Ollama).\n"
        printf "               Sin --yes, cada paso con sudo o descarga pregunta antes.\n\n"
        printf "Variables equivalentes: INSTALL_TOOLS=1 INSTALL_HEAVY=1 ./install.sh\n"
        exit 0
        ;;
      *)
        fail "Flag desconocida: $1 (usa --help)"
        exit 1
        ;;
    esac
    shift
  done
}

# Distribución detectada desde /etc/os-release (o Darwin para macOS).
# Se usa para dar instrucciones correctas por gestor de paquetes.
DISTRO="unknown"
PKG_MGR=""

detect_distro() {
  if [ "$(uname -s)" = "Darwin" ]; then
    DISTRO="macos"
    PKG_MGR="brew"
    return
  fi
  if [ -f /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    case "${ID:-} ${ID_LIKE:-}" in
      *debian*|*ubuntu*) DISTRO="debian"; PKG_MGR="apt" ;;
      *fedora*|*rhel*|*centos*|*rocky*|*alma*) DISTRO="fedora"; PKG_MGR="dnf" ;;
      *arch*|*manjaro*) DISTRO="arch"; PKG_MGR="pacman" ;;
      *suse*|*opensuse*) DISTRO="suse"; PKG_MGR="zypper" ;;
      *alpine*) DISTRO="alpine"; PKG_MGR="apk" ;;
      *) DISTRO="${ID:-unknown}"; PKG_MGR="" ;;
    esac
  fi
  info "Distribución detectada: $DISTRO (gestor: ${PKG_MGR:-ninguno})"
}

# Comando para instalar pip con el gestor de la distribución.
pip_install_hint() {
  case "$DISTRO" in
    debian) printf "    sudo apt install python3-pip python3-venv\n" ;;
    fedora) printf "    sudo dnf install python3-pip\n" ;;
    arch)   printf "    sudo pacman -S python-pip python-virtualenv\n" ;;
    suse)   printf "    sudo zypper install python3-pip python3-virtualenv\n" ;;
    alpine) printf "    sudo apk add py3-pip py3-virtualenv\n" ;;
    macos)  printf "    brew install python\n" ;;
    *)      printf "    Instala pip con el gestor de paquetes de tu distribución\n" ;;
  esac
}

check_python() {
  step "1/7" "Python 3.11+"
  if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJ=$(echo "$PY_VER" | cut -d. -f1)
    PY_MIN=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJ" -ge 3 ] && [ "$PY_MIN" -ge 11 ]; then
      ok "Python $PY_VER"
    else
      fail "Python $PY_VER — se requiere 3.11+"
      exit 1
    fi
  else
    fail "python3 no encontrado. Instala desde https://python.org"
    exit 1
  fi
}

check_pip() {
  step "2/7" "pip"
  if python3 -m pip --version &>/dev/null; then
    ok "pip disponible"
  else
    # No descargamos ni ejecutamos get-pip.py (piping an installer into
    # the interpreter es inseguro y oculta fallos). El usuario debe instalar
    # pip con su gestor de paquetes.
    fail "pip no encontrado."
    printf "  Instálalo con tu gestor de paquetes, por ejemplo:\n"
    pip_install_hint
    exit 1
  fi
}

check_venv() {
  # Debian/Ubuntu separan venv en otro paquete (python3-venv); sin él,
  # `python3 -m venv` falla a mitad de la instalación. Detectarlo aquí
  # da un mensaje claro en vez de un error críptico de ensurepip.
  if ! python3 -c "import venv, ensurepip" 2>/dev/null; then
    fail "python3-venv no disponible."
    printf "  Instálalo con:\n"
    case "$DISTRO" in
      debian) printf "    sudo apt install python3-venv python3-pip\n" ;;
      arch)   printf "    sudo pacman -S python-virtualenv\n" ;;
      suse)   printf "    sudo zypper install python3-virtualenv\n" ;;
      alpine) printf "    sudo apk add py3-virtualenv\n" ;;
      macos)  printf "    brew install python\n" ;;
      *)      printf "    Instala el paquete venv/virtualenv de tu distribución\n" ;;
    esac
    exit 1
  fi
  ok "python3-venv disponible"
}

install_ollama() {
  # Instala Ollama solo si el usuario lo pidió con --all (INSTALL_OLLAMA=1).
  # Nada remoto se ejecuta sin confirmación: en Linux se descarga el
  # instalador OFICIAL a un archivo temporal, se verifica que no esté
  # vacío y solo se ejecuta tras confirmar (o con --yes). Nunca se hace
  # `curl ... | sh` (eso oculta lo que se descarga y lo que se ejecuta).
  if [ "$DISTRO" = "macos" ]; then
    if ! command -v brew &>/dev/null; then
      warn "Homebrew no detectado: instala Ollama a mano desde https://ollama.com/download"
      return 1
    fi
    info "Instalando Ollama con Homebrew..."
    brew install ollama || { warn "brew install ollama falló"; return 1; }
    return 0
  fi
  if [ ! -t 0 ] && [ "$AUTO_YES" != "true" ]; then
    warn "Sin terminal interactiva: no puedo pedir confirmación para instalar Ollama."
    info "Instálalo a mano: https://ollama.com/download"
    return 1
  fi
  if [ "$AUTO_YES" != "true" ]; then
    printf "  Ollama no está instalado. ¿Descargar e instalar el instalador oficial de https://ollama.com? [s/N] "
    local answer=""
    read -r answer || answer=""
    case "$answer" in
      s|S|si|sí|y|Y|yes) ;;
      *) info "Ollama omitido."; return 1 ;;
    esac
  fi
  local tmp_installer
  tmp_installer="$(mktemp /tmp/ollama-install.XXXXXX.sh)"
  info "Descargando instalador oficial de Ollama..."
  if ! curl -fsSL https://ollama.com/install.sh -o "$tmp_installer"; then
    warn "No se pudo descargar el instalador de Ollama."
    rm -f "$tmp_installer"
    return 1
  fi
  if [ ! -s "$tmp_installer" ]; then
    warn "El instalador descargado está vacío."
    rm -f "$tmp_installer"
    return 1
  fi
  info "Ejecutando el instalador oficial (puede pedir sudo)..."
  sh "$tmp_installer" || { warn "El instalador de Ollama falló."; rm -f "$tmp_installer"; return 1; }
  rm -f "$tmp_installer"
  command -v ollama &>/dev/null
}

install_model() {
  # Descarga el modelo ligero por defecto. `ollama pull` arranca el
  # servidor local si hace falta; si falla, solo se avisa.
  if ollama pull qwen2.5-coder:1.5b 2>&1 | tail -n 3; then
    ok "Modelo qwen2.5-coder:1.5b disponible"
  else
    warn "No se pudo descargar el modelo. Intenta a mano: ollama pull qwen2.5-coder:1.5b"
  fi
}

check_ollama() {
  step "3/7" "Ollama (motor AI local)"
  if command -v ollama &>/dev/null; then
    ok "Ollama detectado"
    OLLAMA_OK=true
    if ollama list 2>/dev/null | grep -q "qwen2.5-coder:1.5b"; then
      ok "Modelo qwen2.5-coder:1.5b disponible"
    elif [ "${INSTALL_OLLAMA:-0}" = "1" ]; then
      info "Descargando modelo qwen2.5-coder:1.5b..."
      install_model
    else
      warn "Modelo qwen2.5-coder:1.5b no encontrado"
      info "Descarga con: ${CYN}ollama pull qwen2.5-coder:1.5b${NC}"
    fi
  elif [ "${INSTALL_OLLAMA:-0}" = "1" ]; then
    if install_ollama; then
      OLLAMA_OK=true
      ok "Ollama instalado"
      install_model
    fi
  else
    warn "Ollama no detectado — chat AI no funcionará sin él"
    info "Instala desde: ${CYN}https://ollama.com/download${NC}"
    info "O instálalo todo junto con: ${CYN}./install.sh --all${NC}"
  fi
}

check_tools() {
  step "4/7" "Herramientas Red Team (opcionales)"
  for t in nmap nuclei ffuf subfinder whatweb sqlmap rustscan wpscan; do
    if command -v "$t" &>/dev/null; then
      ok "$t"
    else
      warn "$t no encontrado  ${DIM}(recomendado para recon real)${NC}"
    fi
  done
  install_system_tools
}

# Instalación OPCIONAL de herramientas del sistema, solo con
# INSTALL_TOOLS=1. Pregunta antes de usar sudo y nunca lo usa sin
# confirmación. Solo instala lo que esté en los repositorios de la
# distribución; nuclei, subfinder, rustscan y wpscan no están en la
# mayoría de ellos y se instalan a mano (ver README).
install_system_tools() {
  if [ "${INSTALL_TOOLS:-0}" != "1" ]; then
    info "Herramientas del sistema no instaladas (opcional: INSTALL_TOOLS=1 ./install.sh)"
    return 0
  fi
  local pkgs=""
  case "$DISTRO" in
    debian) pkgs="nmap ffuf sqlmap whatweb" ;;
    fedora) pkgs="nmap ffuf sqlmap whatweb" ;;
    arch)   pkgs="nmap ffuf sqlmap whatweb" ;;
    suse)   pkgs="nmap sqlmap" ;;
    alpine) pkgs="nmap sqlmap" ;;
    macos)  pkgs="nmap sqlmap ffuf whatweb" ;;
    *)
      warn "Distribución no detectada: no sé qué gestor de paquetes usar."
      info "Instala manualmente: nmap, nuclei, ffuf, subfinder, whatweb, sqlmap, rustscan, wpscan"
      return 0
      ;;
  esac
  info "INSTALL_TOOLS=1: se instalarían con sudo ($PKG_MGR): $pkgs"
  info "nuclei, subfinder, rustscan y wpscan no están en estos repositorios; instálalos a mano (ver README)."
  if [ ! -t 0 ] && [ "$AUTO_YES" != "true" ]; then
    warn "Sin terminal interactiva: no puedo pedir confirmación para sudo."
    info "Ejecuta ./install.sh en una terminal o instala las herramientas a mano."
    return 0
  fi
  if [ "$AUTO_YES" != "true" ]; then
    printf "  ¿Instalar con sudo? [s/N] "
    local answer=""
    read -r answer || answer=""
    case "$answer" in
      s|S|si|sí|y|Y|yes) ;;
      *)
        info "Omitido por el usuario."
        return 0
        ;;
    esac
  fi
  case "$PKG_MGR" in
    apt)    sudo apt-get update && sudo apt-get install -y $pkgs || warn "La instalación de herramientas falló" ;;
    dnf)    sudo dnf install -y $pkgs || warn "La instalación de herramientas falló" ;;
    pacman) sudo pacman -S --noconfirm $pkgs || warn "La instalación de herramientas falló" ;;
    zypper) sudo zypper install -y $pkgs || warn "La instalación de herramientas falló" ;;
    apk)    sudo apk add $pkgs || warn "La instalación de herramientas falló" ;;
    brew)   brew install $pkgs || warn "La instalación de herramientas falló" ;;
  esac
}

install_python_deps() {
  step "5/7" "Dependencias Python"
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  
  if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    info "Creando entorno virtual .venv..."
    python3 -m venv "$SCRIPT_DIR/.venv" || { fail "No se pudo crear .venv"; exit 1; }
    ok "Entorno virtual creado"
  else
    ok "Entorno virtual ya existe"
  fi

  # Usar . en lugar de source para máxima compatibilidad
  if ! . "$SCRIPT_DIR/.venv/bin/activate" 2>/dev/null; then
    fail "No se pudo activar .venv desde $SCRIPT_DIR/.venv/bin/activate"
    exit 1
  fi
  
  info "Actualizando pip..."
  python3 -m pip install -q --upgrade pip || warn "Error actualizando pip"

  info "Instalando dependencias core (versiones fijadas en requirements.txt)..."
  # -q para no inundar la pantalla con la lista de paquetes (los errores
  # sí se muestran); cada paso limpia la pantalla al empezar.
  python3 -m pip install -q -r "$SCRIPT_DIR/requirements.txt" || {
    fail "Error instalando dependencias core"
    exit 1
  }
  ok "Core instalado"

  if [ "${INSTALL_HEAVY:-0}" = "1" ]; then
    info "Instalando dependencias ML/AI (esto puede tardar)..."
    # Un paquete por vez: si uno falla, se avisa y se sigue con el
    # resto en lugar de abortar toda la instalación pesada.
    HEAVY_FAILED=""
    for pkg in chromadb sentence-transformers xgboost lightgbm scikit-learn networkx pefile; do
      if python3 -m pip install -q "$pkg"; then
        ok "$pkg instalado"
      else
        warn "$pkg falló — se omite y se sigue con el resto"
        HEAVY_FAILED="$HEAVY_FAILED $pkg"
      fi
    done
    if [ -n "$HEAVY_FAILED" ]; then
      warn "ML/AI parcial: fallaron:$HEAVY_FAILED"
      warn "Las funciones de memoria/RAG que dependen de esos paquetes no estarán disponibles"
    else
      ok "ML/AI instalado"
    fi
  else
    warn "Dependencias ML/AI saltadas"
    info "Actívalas con: ${CYN}INSTALL_HEAVY=1 ./install.sh${NC}"
  fi
}

install_command() {
  step "6/7" "Comando global 'pentia'"
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # El wrapper apunta al directorio DEL REPOSITORIO (PENTIA_HOME), no al
  # directorio donde queda el wrapper. La versión anterior usaba la
  # ubicación del propio wrapper (~/.local/bin) para buscar .venv y
  # pentia.py, y además las comillas escapadas (\\\") dejaban una
  # comilla literal al inicio de la ruta: `pentia` fallaba con
  # `cd: "/home/.../.local/bin: No such file or directory`.
  # Se genera con heredoc entrecomillado (sin expansión) y la ruta del
  # repo se inserta con printf %q, así no hay que escapar comillas a mano.
  INSTALL_PATH=""
  for dir in "$HOME/.local/bin" "$HOME/bin" "/usr/local/bin"; do
    case ":$PATH:" in
      *":$dir:"*)
        if [ -d "$dir" ]; then INSTALL_PATH="$dir"; break; fi ;;
    esac
  done

  if [ -z "$INSTALL_PATH" ]; then
    INSTALL_PATH="$HOME/.local/bin"
    mkdir -p "$INSTALL_PATH"
    warn "~/.local/bin no está en PATH. Agrega a tu shell rc:"
    printf "  ${CYN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}\n"
  fi

  {
    printf '#!/usr/bin/env bash\n'
    printf '# Pentia v4 — generado por install.sh (no editar a mano)\n'
    printf 'set -euo pipefail\n\n'
    printf 'PENTIA_HOME=%s\n' "$(printf '%q' "$SCRIPT_DIR")"
    cat <<'WRAPPER_EOF'
VENV_PATH="$PENTIA_HOME/.venv"

# Validar que .venv existe
if [ ! -f "$VENV_PATH/bin/activate" ]; then
  echo "Error: No se encontró .venv"
  echo "   Ejecuta: cd $PENTIA_HOME && ./install.sh"
  exit 1
fi

# Activar venv y ejecutar
. "$VENV_PATH/bin/activate"
cd "$PENTIA_HOME"
exec python3 "$PENTIA_HOME/pentia.py" "$@"
WRAPPER_EOF
  } > "$INSTALL_PATH/pentia"
  chmod +x "$INSTALL_PATH/pentia"
  ok "Instalado en $INSTALL_PATH/pentia"
}

verify_install() {
  # Prueba el comando generado tal como lo usará el usuario: si el
  # wrapper está roto (ruta, venv, permisos), se detecta aquí y no
  # después, cuando el usuario ya cerró el instalador.
  step "7/7" "Verificación"
  local pentia_bin="${INSTALL_PATH:-$HOME/.local/bin}/pentia"
  if [ ! -x "$pentia_bin" ]; then
    fail "No se generó el comando en $pentia_bin"
    exit 1
  fi
  if "$pentia_bin" version >/dev/null 2>&1; then
    ok "pentia version funciona"
  else
    fail "El comando pentia no arranca. Revisa $pentia_bin y vuelve a correr ./install.sh"
    exit 1
  fi
  if "$pentia_bin" --help >/dev/null 2>&1; then
    ok "pentia --help funciona"
  else
    fail "pentia --help falló."
    exit 1
  fi
}

print_done() {
  printf "\n"
  line
  printf "\n  ${GRN}${BLD}✓ Pentia v4 instalado correctamente${NC}\n\n"
  printf "  ${WHT}Uso rápido:${NC}\n\n"
  printf "  ${CYN}pentia${NC}                     Menú principal\n"
  printf "  ${CYN}pentia --help${NC}              Todos los comandos\n"
  printf "  ${CYN}pentia chat${NC}                IA interactiva en terminal\n"
  printf "  ${CYN}pentia serve${NC}               Web UI en localhost:8000\n"
  printf "  ${CYN}pentia recon <target>${NC}      Pipeline recon completo\n"
  printf "  ${CYN}pentia cve <t> <svc>${NC}      Enriquecimiento CVE\n"
  printf "  ${CYN}pentia web <target>${NC}        Web enumeration\n"
  printf "  ${CYN}pentia version${NC}             Información de versión\n"

  if [ "$OLLAMA_OK" = false ]; then
    printf "\n  ${YLW}⚠ Para el chat AI, instala Ollama:${NC}\n"
    printf "    ${DIM}https://ollama.com/download${NC}\n"
    printf "    ${DIM}ollama pull qwen2.5-coder:1.5b${NC}\n"
  fi

  printf "\n"
  line
  printf "  ${DIM}Si 'pentia' no funciona, recarga tu shell:${NC}\n"
  printf "  ${CYN}source ~/.bashrc${NC}  ${DIM}o${NC}  ${CYN}source ~/.zshrc${NC}\n\n"
}

main() {
  parse_args "$@"
  clear_screen
  print_banner
  detect_distro
  check_python
  check_pip
  check_venv
  check_ollama
  check_tools
  install_python_deps
  install_command
  verify_install
  print_done
}

main "$@"
