# FAQ & Troubleshooting - Pentia v4

## ❓ Preguntas Frecuentes

### P: ¿Funciona en Windows?
R: Parcialmente. El instalador está diseñado para Linux/macOS. En Windows puedes:
- Usar WSL 2 (recomendado)
- Usar Docker (próximamente)
- Instalar manualmente en Windows PowerShell

### P: ¿Necesito Ollama obligatoriamente?
R: No para todas las features. Sin Ollama:
- ✓ Todos los pipelines de scanning funcionan
- ✓ Inteligencia CVE funciona
- ✓ Reportes funcionan
- ✗ Chat AI no funciona

### P: ¿Puedo usar otro modelo LLM?
R: Sí. Cualquier modelo que Ollama soporte:
```bash
ollama pull mistral
ollama pull llama2
pentia chat --model mistral
```

### P: ¿Cuánta RAM necesito?
R: Depende de uso:
- **Básico (sin ML)**: 4 GB
- **Con ML**: 16 GB+
- **Modelos grandes**: 32 GB+

### P: ¿Funciona sin herramientas externas?
R: Algunos pipelines necesitan herramientas específicas:
- nmap para port scanning
- ffuf para fuzzing
- nuclei para vulnerability scanning
- Puedes usar los que tengas instalados

### P: ¿Cómo actualizo Pentia?
R: 
```bash
cd /ruta/pentia
git pull origin main
./install.sh  # Si hay nuevas dependencias
```

---

## 🐛 Troubleshooting

### "pentia: command not found"

**Causa**: Comando no está en PATH

**Soluciones**:

1. Verifica que ~/.local/bin existe:
```bash
ls -la ~/.local/bin/pentia
```

2. Si no existe, reinstala:
```bash
cd /ruta/pentia
./install.sh
```

3. Agrega a tu PATH (~/.bashrc o ~/.zshrc):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

4. Recarga shell:
```bash
source ~/.bashrc
# o
source ~/.zshrc
```

---

### "No existe el fichero o directorio" (.venv/bin/activate)

**Causa**: El .venv no se creó correctamente

**Soluciones**:

```bash
# 1. Limpiar y reinstalar
cd /ruta/pentia
rm -rf .venv
rm ~/.local/bin/pentia

# 2. Reinstalar
./install.sh

# 3. Verificar que existe
ls -la .venv/bin/activate
```

Si sigue fallando:
```bash
# Crear manualmente
python3 -m venv .venv
. .venv/bin/activate
pip install -q typer[all] rich httpx fastapi uvicorn pydantic requests
```

---

### "Ollama connection refused"

**Causa**: Ollama no está corriendo

**Soluciones**:

1. Inicia Ollama en otra terminal:
```bash
ollama serve
```

2. Verifica que responde:
```bash
curl http://localhost:11434/api/tags
```

3. Si no conecta, verifica el puerto:
```bash
lsof -i :11434  # ¿Está usando el puerto?
```

4. En macOS/Linux, verifica que Ollama está instalado:
```bash
which ollama
ollama --version
```

---

### "Modelo no encontrado"

**Causa**: El modelo no está descargado

**Soluciones**:

1. Descarga el modelo:
```bash
ollama pull qwen2.5-coder
```

2. Lista modelos disponibles:
```bash
ollama list
```

3. Usa otro modelo:
```bash
pentia chat --model mistral
```

---

### "Error: Chromadb not available"

**Causa**: Dependencias ML no instaladas

**Soluciones**:

1. Instala dependencias pesadas:
```bash
INSTALL_HEAVY=1 ./install.sh
```

2. O manualmente:
```bash
source .venv/bin/activate
pip install chromadb sentence-transformers
```

3. Si falla por compiladores, instala:

**Ubuntu/Debian**:
```bash
sudo apt-get install build-essential python3-dev
```

**macOS**:
```bash
xcode-select --install
```

**Fedora**:
```bash
sudo dnf install gcc gcc-c++ python3-devel
```

---

### "ImportError: No module named 'scanners.nmap'"

**Causa**: nmap no está instalado o no en PATH

**Soluciones**:

1. Instala nmap:

**Ubuntu/Debian**:
```bash
sudo apt-get install nmap
```

**macOS**:
```bash
brew install nmap
```

**Fedora**:
```bash
sudo dnf install nmap
```

2. Verifica que está accesible:
```bash
which nmap
nmap --version
```

---

### "Web UI no carga (ui.html no encontrado)"

**Causa**: Archivo ui.html está corrupto o falta

**Soluciones**:

1. Verifica que existe:
```bash
ls -la web/ui.html
```

2. Si no existe:
```bash
# Reinstala desde git
git checkout web/ui.html
```

3. Si sigue fallando, recrea desde backup:
```bash
git status  # Ver qué cambió
git restore web/ui.html
```

---

### "Error: Invalid target"

**Causa**: Input no es válido

**Soluciones**:

1. Verifica el formato:
```bash
pentia recon example.com           # ✓ Valido
pentia recon https://example.com   # ✓ Valido
pentia recon "example com"         # ✗ Inválido (espacios)
```

2. Limpia input:
```bash
pentia recon example.com -f
```

---

### "Error: Timeout"

**Causa**: Operación tardó demasiado

**Soluciones**:

1. Usa modo rápido:
```bash
pentia recon example.com -f
```

2. Aumenta timeout (si es posible):
```bash
timeout 600 pentia recon example.com
```

3. Revisa conexión a internet:
```bash
ping 8.8.8.8
```

---

### "Memory usage very high"

**Causa**: Bases de datos vectoriales o modelos grandes

**Soluciones**:

1. Limpia caché:
```bash
rm -rf .pentia_memory/
```

2. Reduce modelo ML:
```bash
# Usa modelo más pequeño
pentia chat --model qwen2.5:1.5b
```

3. Monitorea memoria:
```bash
watch -n 1 free -h
```

---

### "Error al descargar inteligencia"

**Causa**: Conexión de internet o API limit

**Soluciones**:

1. Verifica conexión:
```bash
ping nist.gov
```

2. Reintenta después:
```bash
pentia intel-download --kev
```

3. Descarga manualmente de NIST:
```bash
# https://nvlpubs.nist.gov/vuln/data-feeds
```

---

## 🔧 Debugging Avanzado

### Ver logs detallados
```bash
PYTHONPATH=. python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from pentia import app
" --help
```

### Profiling de performance
```python
import cProfile
import pstats
from pentia import app

pr = cProfile.Profile()
pr.enable()
# [Tu código aquí]
pr.disable()

ps = pstats.Stats(pr)
ps.sort_stats('cumulative')
ps.print_stats(20)
```

### Inspeccionar módulos
```bash
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from core import ai, memory, intel
print('✓ Módulos cargan correctamente')
"
```

---

## 📞 Obtener Ayuda

1. **Lee la documentación**: README.md, DEVELOPMENT.md
2. **Busca issues existentes**: GitHub Issues
3. **Abre un issue**: Incluye logs y contexto
4. **Sé específico**: Pasos para reproducir, ambiente, etc.

---

**Última actualización**: Mayo 2026
