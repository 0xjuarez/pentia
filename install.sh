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
    info "Instalando pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3 -
    ok "pip instalado"
  fi
}

check_ollama() {
  step "3/6" "Ollama (motor AI local)"
  if command -v ollama &>/dev/null; then
    ok "Ollama detectado"
    OLLAMA_OK=true
    if ollama list 2>/dev/null | grep -q "qwen2.5-coder"; then
      ok "Modelo qwen2.5-coder disponible"
    else
      warn "Modelo qwen2.5-coder no encontrado"
      info "Descarga con: ${CYN}ollama pull qwen2.5-coder${NC}"
    fi
  else
    warn "Ollama no detectado — chat AI no funcionará sin él"
    info "Instala desde: ${CYN}https://ollama.com/download${NC}"
  fi
}

check_tools() {
  step "4/6" "Herramientas Red Team (opcionales)"
  for t in nmap nuclei ffuf subfinder whatweb sqlmap; do
    if command -v "$t" &>/dev/null; then
      ok "$t"
    else
      warn "$t no encontrado  ${DIM}(recomendado para recon real)${NC}"
    fi
  done
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
  python3 -m pip install -q --upgrade pip 2>/dev/null || warn "Error actualizando pip"

  info "Instalando dependencias core..."
  python3 -m pip install -q typer"[all]" rich httpx fastapi uvicorn pydantic requests 2>/dev/null || {
    fail "Error instalando dependencias core"
    exit 1
  }
  ok "Core instalado"

  if [ "${INSTALL_HEAVY:-0}" = "1" ]; then
    info "Instalando dependencias ML/AI (esto puede tardar)..."
    python3 -m pip install -q chromadb sentence-transformers xgboost lightgbm scikit-learn networkx faiss-cpu pefile 2>/dev/null || {
      warn "Algunos paquetes ML/AI fallaron (esto es normal si falta compiladores)"
    }
    ok "ML/AI instalado"
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
    printf "    ${DIM}ollama pull qwen2.5-coder${NC}\n"
  fi

  printf "\n"
  line
  printf "  ${DIM}Si 'pentia' no funciona, recarga tu shell:${NC}\n"
  printf "  ${CYN}source ~/.bashrc${NC}  ${DIM}o${NC}  ${CYN}source ~/.zshrc${NC}\n\n"
}

main() {
  print_banner
  check_python
  check_pip
  check_ollama
  check_tools
  install_python_deps
  install_command
  print_done
}

main "$@"
