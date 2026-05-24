# Contribuyendo a Pentia v4

Gracias por tu interés en contribuir a Pentia. Este documento te guía sobre cómo hacerlo.

## Código de Conducta

Sé respetuoso con otros contribuyentes. Queremos un ambiente inclusivo y acogedor.

## Cómo Contribuir

### 1. Fork el repositorio
```bash
# Haz un fork en GitHub
git clone https://github.com/tu-usuario/pentia.git
cd pentia
```

### 2. Crea una rama
```bash
git checkout -b feature/mi-feature
# o para bugs:
git checkout -b bugfix/problema-a-arreglar
```

### 3. Desarrolla e implementa tests
```bash
# Instala con dependencias pesadas
INSTALL_HEAVY=1 ./install.sh

# Crea tus cambios
# ... código ...

# Prueba localmente
pentia --help
pentia chat
```

### 4. Commit y Push
```bash
git add .
git commit -m "Descripción clara del cambio"
git push origin feature/mi-feature
```

### 5. Pull Request
- Abre un PR en GitHub
- Describe el problema y la solución
- Menciona cualquier issue relacionado (#123)

## Guías de Estilo

### Python
- Python 3.11+
- Type hints en todas las funciones
- Usa f-strings para formatear
- Sigue PEP 8
- Máximo 120 caracteres de línea

```python
async def my_function(target: str, timeout: int = 30) -> dict:
    """
    Descripción clara de qué hace.
    
    Args:
        target: Descripción del parámetro
        timeout: Tiempo máximo en segundos
    
    Returns:
        Diccionario con resultados
    """
    try:
        # Tu implementación
        pass
    except Exception as e:
        logger.error(f"Error procesando {target}: {e}")
        raise
```

### Commit Messages
```
[tipo]: Descripción breve (máximo 50 caracteres)

Descripción más detallada si es necesario.
Explica el QUÉ y el POR QUÉ, no el CÓMO.

- Punto 1
- Punto 2

Fixes #123
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Manejo de Errores
Siempre maneja errores de forma elegante:
```python
try:
    result = await dangerous_operation()
except SpecificError as e:
    logger.error(f"Error específico: {e}")
    # Recuperación o fallback
except Exception as e:
    logger.exception(f"Error inesperado: {e}")
    raise
```

## Áreas Donde Necesitamos Ayuda

### 🐛 Bug Fixes
- Reporta bugs en Issues con pasos de reproducción
- Proporciona logs y contexto

### ✨ Nuevos Scanners
Agrega un scanner en `scanners/`:
```python
# scanners/mi_scanner.py
from typing import Dict, List

async def scan(target: str) -> Dict:
    """Implementar tu scanner aquí"""
    return {"results": [], "status": "ok"}
```

### 🔌 Plugins Personalizados
Crea en `plugins/custom/`:
```python
from plugins.base import ScannerBase

class MiPlugin(ScannerBase):
    async def scan(self, target: str):
        return await self.execute(["comando", target])
```

### 📚 Documentación
- Mejora el README
- Agrega ejemplos
- Documenta nuevas features
- Corrige typos

### 🧪 Tests
Aunque no tenemos tests automatizados aún, puedes:
- Testear cambios localmente
- Reportar casos edge
- Proponer estructura de tests

## Área de Desarrollo (dev)

Para desarrollo activo:
```bash
# Instala en modo editable
pip install -e .

# Usa logging para debug
PYTHONPATH=. python3 -c "import logging; logging.basicConfig(level=logging.DEBUG); from pentia import *"
```

## Reportar Bugs

Abre un Issue con:
1. **Descripción clara** del problema
2. **Pasos para reproducir**
3. **Comportamiento esperado vs actual**
4. **Environment**: Python version, OS, Ollama status
5. **Logs**: Output relevante (sin tokens/keys)

```markdown
## Descripción
[Describe el problema]

## Pasos para reproducir
1. Ejecuta `pentia ...`
2. Ocurre...

## Esperado
[Lo que debería pasar]

## Actual
[Lo que realmente pasó]

## Sistema
- OS: Linux 5.15
- Python: 3.11.4
- Ollama: Running
```

## Sugerencias de Mejora

Abre un Issue con la etiqueta `enhancement`:
- Describe el feature
- Explicar el caso de uso
- Si es posible, ofrece una solución

## Preguntas

Preguntas sobre código, instalación, etc:
- Issues con etiqueta `question`
- Sé específico para que otros puedan ayudarte

## Reconocimiento

Todos los contribuyentes serán reconocidos en:
- [CONTRIBUTORS.md](CONTRIBUTORS.md) (proximamente)
- Commits y PRs

## Licencia

Al contribuir, aceptas que tu código puede ser usado bajo los términos del proyecto.

---

¡Gracias por contribuir a Pentia! 🚀
