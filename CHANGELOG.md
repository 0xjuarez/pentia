# Changelog - Pentia v4

Todos los cambios notables en este proyecto serán documentados en este archivo.

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

### ⚠️ Por Hacer (Roadmap)
- [ ] Tests unitarios y de integración
- [ ] Caché persistente para resultados
- [ ] WebSockets para actualizaciones en tiempo real
- [ ] Autenticación en Web UI
- [ ] API autenticada
- [ ] Dashboard de estadísticas
- [ ] Export a formatos adicionales (HTML, PDF)
- [ ] Paralelización mejorada
- [ ] GPU acceleration para ML
- [ ] Integración con más herramientas

### 📦 Dependencias
- Python 3.11+
- Ollama (opcional, para chat)
- Herramientas: nmap, nuclei, ffuf, etc. (opcional)
- ML: chromadb, transformers, xgboost (opcional)

---

## Versiones Anteriores

- **v3.x**: Arquitectura anterior (deprecada)
- **v2.x**: Primera generación (archived)
