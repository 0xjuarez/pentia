#!/usr/bin/env bash
# ============================================================
#  PENTIA v4 — Red Team AI Platform  |  install.sh
#  DevSecurityMX · Jesús Juárez
# ============================================================
set -euo pipefail

RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'
CYN='\033[0;36m'; WHT='\033[1;37m'; MGN='\033[0;35m'
BLU='\033[0;34m'; DIM='\033[2m'; BLD='\033[1m'; NC='\033[0m'

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
step() { printf "\n  ${BLD}${WHT}[$1]${NC} ${WHT}$2${NC}\n"; }
line() { printf "  ${DIM}────────────────────────────────────────────${NC}\n"; }

OLLAMA_OK=false

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
  step "1/6" "Python 3.11+"
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
  step "2/6" "pip"
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

check_ollama() {
  step "3/6" "Ollama (motor AI local)"
  if command -v ollama &>/dev/null; then
    ok "Ollama detectado"
    OLLAMA_OK=true
    if ollama list 2>/dev/null | grep -q "qwen2.5-coder:1.5b"; then
      ok "Modelo qwen2.5-coder:1.5b disponible"
    else
      warn "Modelo qwen2.5-coder:1.5b no encontrado"
      info "Descarga con: ${CYN}ollama pull qwen2.5-coder:1.5b${NC}"
    fi
  else
    warn "Ollama no detectado — chat AI no funcionará sin él"
    info "Instala desde: ${CYN}https://ollama.com/download${NC}"
  fi
}

check_tools() {
  step "4/6" "Herramientas Red Team (opcionales)"
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
  if [ ! -t 0 ]; then
    warn "Sin terminal interactiva: no puedo pedir confirmación para sudo."
    info "Ejecuta ./install.sh en una terminal o instala las herramientas a mano."
    return 0
  fi
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
  step "5/6" "Dependencias Python"
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
  python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" || {
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
  step "6/6" "Comando global 'pentia'"
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # Wrapper mejorado que maneja errores correctamente
  WRAPPER="#!/usr/bin/env bash
# Pentia v4 — generado por install.sh
set -euo pipefail

SCRIPT_DIR=\"\$(cd \"\$(dirname \\\"\${BASH_SOURCE[0]}\\\")\" && pwd)\"
PENTIA_HOME=\"$SCRIPT_DIR\"
VENV_PATH=\"\$PENTIA_HOME/.venv\"

# Validar que .venv existe
if [ ! -f \"\$VENV_PATH/bin/activate\" ]; then
  echo \"❌ Error: No se encontró .venv\"
  echo \"   Ejecuta: cd \$PENTIA_HOME && ./install.sh\"
  exit 1
fi

# Activar venv y ejecutar
. \"\$VENV_PATH/bin/activate\"
cd \"\$PENTIA_HOME\"
exec python3 \"\$PENTIA_HOME/pentia.py\" \"\$@\""

  INSTALL_PATH=""
  for dir in "$HOME/.local/bin" "$HOME/bin" "/usr/local/bin"; do
    if [ -d "$dir" ] && echo "$PATH" | grep -q "$dir"; then
      INSTALL_PATH="$dir"
      break
    fi
  done

  if [ -z "$INSTALL_PATH" ]; then
    INSTALL_PATH="$HOME/.local/bin"
    mkdir -p "$INSTALL_PATH"
    warn "~/.local/bin no está en PATH. Agrega a tu shell rc:"
    printf "  ${CYN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}\n"
  fi

  printf "%s\n" "$WRAPPER" > "$INSTALL_PATH/pentia"
  chmod +x "$INSTALL_PATH/pentia"
  ok "Instalado en $INSTALL_PATH/pentia"
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
  print_banner
  detect_distro
  check_python
  check_pip
  check_venv
  check_ollama
  check_tools
  install_python_deps
  install_command
  print_done
}

main "$@"
