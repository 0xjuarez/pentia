#!/usr/bin/env python3
"""
Pentia v4 — Red Team AI Platform
CLI entry point con manejo robusto de errores
"""
from __future__ import annotations
import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pentia")

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from core.orchestrator import Orchestrator
    from core.cve_intelligence import CVEIntelligence
    from core.memory import MemoryStore
    from core.intel import enrich_service
    from core.scoring import score_finding
    from reports.generator import write_reports
    import pipelines.recon as recon_pipeline
    import pipelines.web as web_pipeline
    import pipelines.internal as internal_pipeline
    import pipelines.malware as malware_pipeline
except ImportError as e:
    logger.warning(f"Algunos módulos no están disponibles: {e}")
    # Continuar de todos modos, algunos comandos funcionarán

app = typer.Typer(
    name="pentia",
    help="[bold green]Pentia v4[/] — Red Team AI Platform",
    rich_markup_mode="rich",
    no_args_is_help=False,
    add_completion=True,
)
console = Console()

BANNER = """[bold red]██████╗ [bold yellow] ███████╗[bold green]███╗   ██╗[bold cyan]████████╗[bold blue]██╗ [bold magenta] █████╗ [/]
[bold red]██╔══██╗[bold yellow]██╔════╝[bold green]████╗  ██║[bold cyan]╚══██╔══╝[bold blue]██║[bold magenta]██╔══██╗[/]
[bold red]██████╔╝[bold yellow]█████╗  [bold green]██╔██╗ ██║[bold cyan]   ██║   [bold blue]██║[bold magenta]███████║[/]
[bold red]██╔═══╝ [bold yellow]██╔══╝  [bold green]██║╚██╗██║[bold cyan]   ██║   [bold blue]██║[bold magenta]██╔══██║[/]
[bold red]██║     [bold yellow]███████╗[bold green]██║ ╚████║[bold cyan]   ██║   [bold blue]██║[bold magenta]██║  ██║[/]
[bold red]╚═╝     [bold yellow]╚══════╝[bold green]╚═╝  ╚═══╝[bold cyan]   ╚═╝   [bold blue]╚═╝[bold magenta]╚═╝  ╚═╝[/]"""

DIVIDER = "[dim]─────────────────────────────────────────────────────[/]"


def show_banner():
    console.print(BANNER)
    console.print("[bold white]  v4[/] [dim]·[/] [bold green]Red Team AI Platform[/]")
    console.print(DIVIDER)


def show_header(command: str = "", target: str = ""):
    show_banner()
    if command:
        parts = f"[bold white]>[/] [bold cyan]{command}[/]"
        if target:
            parts += f"  [dim]→[/]  [bold yellow]{target}[/]"
        console.print(parts)
        console.print()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """[bold green]Pentia v4[/] — Red Team AI Platform by DevSecurityMX"""
    if ctx.invoked_subcommand is None:
        show_banner()
        console.print()
        console.print(Panel(
            "[bold]Comandos disponibles:[/]\n\n"
            "  [bold cyan]pentia recon[/] [yellow]<target>[/]              Full recon pipeline\n"
            "  [bold cyan]pentia web[/] [yellow]<target>[/]                Web enumeration\n"
            "  [bold cyan]pentia internal[/] [yellow]<network>[/]          Red interna\n"
            "  [bold cyan]pentia malware[/] [yellow]<sample>[/]            Análisis de malware\n"
            "  [bold cyan]pentia cve[/] [yellow]<target> <service>[/]      Enriquecimiento CVE\n"
            "  [bold cyan]pentia intel[/] [yellow]<query>[/]               Búsqueda intel local\n"
            "  [bold cyan]pentia memory[/] [yellow]<query>[/]              Consulta memoria RAG\n"
            "  [bold cyan]pentia chat[/]                        IA interactiva (terminal)\n"
            "  [bold cyan]pentia serve[/]                       Interfaz web (localhost:8000)\n"
            "  [bold cyan]pentia report[/] [yellow]<summary>[/]            Generar reporte\n"
            "  [bold cyan]pentia intel-download[/]              Descargar KEV/NVD\n"
            "  [bold cyan]pentia version[/]                     Información de versión\n\n"
            "[dim]Usa [bold]pentia <comando> --help[/] para opciones detalladas.[/]",
            title="[bold red]⚡ Pentia[/] [bold white]v4[/]",
            border_style="bold green",
            padding=(1, 2),
        ))


@app.command()
def recon(
    target: str = typer.Argument(..., help="Target IP, dominio o CIDR"),
    fast: bool = typer.Option(False, "--fast", "-f", help="Omitir checks lentos"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Directorio de reporte"),
):
    """[bold]Full recon pipeline[/]: nmap → nuclei → subfinder → ffuf → CVE enrichment."""
    show_header("recon", target)
    memory = MemoryStore()
    orchestrator = Orchestrator()
    with console.status(f"[bold green]Ejecutando recon sobre {target}...[/]", spinner="dots"):
        results = asyncio.run(recon_pipeline.run_recon_pipeline(target, memory, orchestrator, fast=fast))
    _print_results_table("Recon Results", target, results)
    if output:
        write_reports(str(results), output_dir=output)
        console.print(f"\n[bold green]✓[/] Reporte guardado en [bold]{output}[/]")


@app.command()
def web(
    target: str = typer.Argument(..., help="URL o dominio objetivo"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """[bold]Web enumeration[/]: whatweb → ffuf → nuclei → wpscan."""
    show_header("web", target)
    with console.status(f"[bold cyan]Enumerando web en {target}...[/]", spinner="bouncingBar"):
        results = asyncio.run(web_pipeline.run_web_pipeline(target))
    _print_results_table("Web Enum Results", target, results)
    if output:
        write_reports(str(results), output_dir=output)


@app.command()
def internal(
    network: str = typer.Argument(..., help="Red interna (ej. 192.168.1.0/24)"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """[bold]Internal network recon[/]: ARP → SMB → AD → Bloodhound."""
    show_header("internal", network)
    with console.status(f"[bold magenta]Enumerando red interna {network}...[/]", spinner="arc"):
        results = asyncio.run(internal_pipeline.run_internal_pipeline(network))
    _print_results_table("Internal Enum", network, results)
    if output:
        write_reports(str(results), output_dir=output)


@app.command()
def malware(
    sample_path: str = typer.Argument(..., help="Ruta a la muestra PE"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """[bold]Malware analysis[/]: PE features → entropy → clasificación neuronal."""
    show_header("malware", sample_path)
    if not Path(sample_path).exists():
        console.print(f"[bold red]✗[/] Archivo no encontrado: {sample_path}")
        raise typer.Exit(1)
    with console.status("[bold red]Analizando muestra...[/]", spinner="earth"):
        results = asyncio.run(malware_pipeline.run_malware_pipeline(sample_path))

    features = results.get("features", {})
    prediction = results.get("prediction", {})
    label = prediction.get("label", "unknown")
    confidence = prediction.get("confidence", 0)
    color = "red" if label in ("ransomware/stealer", "loader/crypter") else "yellow"

    table = Table(title=f"Malware Analysis — {Path(sample_path).name}", box=box.ROUNDED, border_style="red")
    table.add_column("Feature", style="bold cyan")
    table.add_column("Valor")
    for k, v in features.items():
        if k != "import_names":
            table.add_row(k, str(v))
    console.print(table)
    console.print(Panel(
        f"[bold]Clasificación:[/] [{color}]{label}[/]\n[bold]Confianza:[/]    {confidence:.0%}",
        title="[bold red]⚠ Resultado Neural[/]", border_style=color,
    ))
    imports = features.get("import_names", [])
    if imports:
        console.print(f"\n[dim]Imports:[/] {', '.join(imports[:15])}{'...' if len(imports) > 15 else ''}")
    if output:
        write_reports(str(results), output_dir=output)


@app.command()
def cve(
    target: str = typer.Argument(..., help="Target IP o hostname"),
    service: str = typer.Argument(..., help="Servicio detectado (ej. Apache)"),
    version: Optional[str] = typer.Argument(None, help="Versión (ej. 2.4.49)"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """[bold]CVE enrichment[/]: CPE → NVD → KEV → ExploitDB → Nuclei → scoring."""
    show_header("cve", f"{target}  [{service} {version or ''}]")
    with console.status("[bold yellow]Enriqueciendo con inteligencia CVE...[/]", spinner="clock"):
        result = asyncio.run(enrich_service(target, service, version))

    cves = result.get("cves", [])
    cpe = result.get("cpe", "N/A")
    console.print(f"[bold]CPE detectado:[/] [cyan]{cpe}[/]")
    console.print(f"[bold]CVEs encontrados:[/] [{'red' if cves else 'green'}]{len(cves)}[/]\n")

    if not cves:
        console.print("[green]✓ Sin CVEs críticos detectados.[/]")
    else:
        table = Table(title="CVE Findings", box=box.ROUNDED, border_style="yellow")
        table.add_column("CVE ID", style="bold red", min_width=16)
        table.add_column("CVSS", justify="center")
        table.add_column("Severity", justify="center")
        table.add_column("KEV", justify="center")
        table.add_column("Exploit", justify="center")
        table.add_column("MSF", justify="center")
        table.add_column("Score", justify="center")
        for c in sorted(cves, key=lambda x: x.get("cvss") or 0, reverse=True):
            cvss = c.get("cvss") or 0
            sev = c.get("severity", "")
            sev_color = {"CRITICAL": "red", "HIGH": "orange3", "MEDIUM": "yellow", "LOW": "green"}.get(sev, "white")
            s = score_finding(c)
            score_color = "red" if s.get("label") == "high" else "yellow" if s.get("label") == "medium" else "green"
            table.add_row(
                c.get("id", "?"),
                f"[bold]{cvss:.1f}[/]",
                f"[{sev_color}]{sev}[/]",
                "[red]✓[/]" if c.get("kev") else "[dim]–[/]",
                "[red]✓[/]" if c.get("exploit_available") else "[dim]–[/]",
                "[red]✓[/]" if c.get("metasploit") else "[dim]–[/]",
                f"[{score_color}]{s.get('score', 0):.2f}[/]",
            )
        console.print(table)
        if result.get("_cache_path"):
            console.print(f"\n[dim]Findings cacheados en: {result['_cache_path']}[/]")

    if output:
        write_reports(str(result), output_dir=output)


@app.command()
def intel(query: str = typer.Argument(..., help="Consulta (ej. 'apache RCE')")):
    """[bold]Buscar en intel CVE local[/] (NVD + ExploitDB + KEV)."""
    show_header("intel", query)
    memory = MemoryStore(collection_name="cve_intel")
    intel_engine = CVEIntelligence(memory=memory)
    with console.status("[bold cyan]Consultando inteligencia local...[/]", spinner="dots12"):
        summary = asyncio.run(intel_engine.summarize(query))
    console.print(Panel(
        summary or "[dim]Sin resultados. Usa pentia ingest-intel para cargar datos.[/]",
        title=f"[bold]Intel:[/] {query}",
        border_style="cyan", padding=(1, 2),
    ))


@app.command("memory")
def memory_cmd(
    query: str = typer.Argument(..., help="Consulta semántica"),
    top_k: int = typer.Option(5, "--top", "-k"),
):
    """[bold]Consultar memoria semántica RAG[/] (ChromaDB local)."""
    show_header("memory", query)
    mem = MemoryStore()
    with console.status("[bold blue]Buscando en memoria...[/]", spinner="point"):
        results = asyncio.run(mem.retrieve(query, k=top_k))
    if not results:
        console.print("[yellow]Sin resultados.[/] Usa [bold]pentia ingest-intel[/] para cargar datos.")
        return
    for i, item in enumerate(results, 1):
        console.print(Panel(
            item.get("text", ""),
            title=f"[cyan]Resultado {i}[/]  [dim]{item.get('metadata', {})}[/]",
            border_style="blue", padding=(0, 1),
        ))


@app.command("ingest-intel")
def ingest_intel(path: str = typer.Argument(..., help="Archivo NVD JSON o ExploitDB CSV")):
    """[bold]Ingestar inteligencia local[/] en memoria RAG."""
    show_header("ingest-intel", path)
    if not Path(path).exists():
        console.print(f"[red]✗ Archivo no encontrado:[/] {path}")
        raise typer.Exit(1)
    memory = MemoryStore()
    intel_engine = CVEIntelligence(memory=memory)
    with console.status("[bold green]Ingiriendo...[/]", spinner="dots"):
        if path.endswith(".json"):
            count = asyncio.run(intel_engine.ingest_nvd_file(path))
            console.print(f"[green]✓[/] Ingestados [bold]{count}[/] registros NVD.")
        else:
            count = asyncio.run(intel_engine.ingest_exploitdb_file(path))
            console.print(f"[green]✓[/] Ingestados [bold]{count}[/] registros ExploitDB.")


@app.command("intel-download")
def intel_download(
    kev: bool = typer.Option(False, "--kev"),
    nvd_url: Optional[str] = typer.Option(None, "--nvd-url"),
    out: str = typer.Option("datasets", "--out", "-o"),
):
    """[bold]Descargar feeds[/] CISA KEV y/o NVD."""
    show_header("intel-download")
    import subprocess
    args = [sys.executable, "scripts/download_intel.py", "--out", out]
    if kev:
        args.append("--kev")
    if nvd_url:
        args += ["--nvd-url", nvd_url]
    with console.status("[bold green]Descargando...[/]", spinner="earth"):
        result = subprocess.run(args, capture_output=True, text=True)
    console.print(f"[green]✓[/] {result.stdout.strip()}" if result.returncode == 0 else f"[red]✗[/] {result.stderr.strip()}")


@app.command()
def report(
    summary: str = typer.Argument(..., help="Resumen o ruta a JSON"),
    output: str = typer.Option("reports", "--output", "-o"),
):
    """[bold]Generar reporte[/] en Markdown y JSON."""
    show_header("report")
    findings = None
    if Path(summary).exists():
        import json
        try:
            with open(summary) as f:
                data = json.load(f)
            findings = data.get("findings") if isinstance(data, dict) else None
            summary = data.get("summary", str(data)) if isinstance(data, dict) else str(data)
        except Exception:
            pass
    paths = write_reports(summary, findings=findings, output_dir=output)
    table = Table(title="Reportes generados", box=box.SIMPLE, border_style="green")
    table.add_column("Formato", style="bold cyan")
    table.add_column("Ruta")
    for fmt_name, path in paths.items():
        table.add_row(fmt_name.upper(), path)
    console.print(table)


@app.command()
def chat(
    model: str = typer.Option("qwen2.5-coder", "--model", "-m"),
    memory_enabled: bool = typer.Option(True, "--memory/--no-memory"),
):
    """[bold]Sesión AI interactiva[/] en terminal (requiere Ollama)."""
    show_banner()
    console.print()
    console.print(Panel(
        f"[bold]Modelo:[/] [cyan]{model}[/]  [dim]|[/]  "
        f"[bold]Memoria:[/] {'[green]ON[/]' if memory_enabled else '[dim]OFF[/]'}\n\n"
        "[dim]/exit salir · /clear limpiar · /memory <q> buscar en RAG[/]",
        title="[bold red]PENTIA[/] [bold white]Chat[/]",
        border_style="red", padding=(1, 2),
    ))
    from core.ai import LLMClient
    llm = LLMClient(model=model)
    mem = MemoryStore() if memory_enabled else None

    while True:
        try:
            user_input = console.input("\n[bold green]▶ [/]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Sesión terminada.[/]")
            break
        if not user_input:
            continue
        if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]Bye.[/]")
            break
        if user_input.lower() == "/clear":
            console.clear()
            show_banner()
            continue
        if user_input.lower().startswith("/memory "):
            q = user_input[8:]
            if mem:
                items = asyncio.run(mem.retrieve(q, k=3))
                for r in items:
                    console.print(Panel(r.get("text", ""), border_style="blue"))
            continue

        context = None
        if mem:
            try:
                items = asyncio.run(mem.retrieve(user_input, k=3))
                if items:
                    context = "\n\n".join(i.get("text", "") for i in items)
            except Exception:
                pass

        with console.status("[dim]Procesando...[/]", spinner="dots"):
            try:
                response = asyncio.run(llm.generate(user_input, context=context))
            except Exception as e:
                response = f"Error: {e}\n\n¿Ollama está corriendo? Ejecuta: [bold]ollama serve[/]"

        console.print()
        console.print(Panel(response, title="[bold red]PENTIA[/] [bold white]AI[/]", border_style="dim", padding=(0, 1)))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-H"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload"),
):
    """[bold]Lanzar interfaz web[/] (localhost:8000)."""
    show_banner()
    console.print()
    console.print(Panel(
        f"[bold]URL:[/] [cyan]http://{host}:{port}[/]\n\n[dim]Ctrl+C para detener[/]",
        title="[bold green]⚡ Pentia Web UI[/]", border_style="green", padding=(1, 2),
    ))
    try:
        import uvicorn
        from web.app import create_app
        uvicorn.run(create_app(), host=host, port=port, reload=reload)
    except ImportError as e:
        console.print(f"[red]✗[/] Dependencia faltante: {e}")


@app.command()
def version():
    """Información de versión."""
    show_banner()
    console.print(f"\n  [bold]Versión:[/]   [green]4.0.0[/]")
    console.print(f"  [bold]Python:[/]    [cyan]{sys.version.split()[0]}[/]")
    console.print(f"  [bold]Platform:[/]  [cyan]{sys.platform}[/]")
    console.print(f"  [bold]Estado:[/]    [yellow]En desarrollo[/]")


def _print_results_table(title: str, target: str, results):
    table = Table(title=f"{title} — {target}", box=box.ROUNDED, border_style="cyan")
    table.add_column("Módulo", style="bold cyan", min_width=12)
    table.add_column("Resultado")
    table.add_column("Estado", justify="center")
    if isinstance(results, dict):
        for key, value in results.items():
            if isinstance(value, Exception):
                table.add_row(str(key), str(value)[:100], "[red]✗[/]")
            elif value:
                table.add_row(str(key), str(value)[:120], "[green]✓[/]")
            else:
                table.add_row(str(key), "[dim]–[/]", "[yellow]⚠[/]")
    else:
        table.add_row("resultado", str(results)[:200], "[green]✓[/]")
    console.print(table)


def main():
    """Entry point con manejo de errores global"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupción del usuario[/]")
        sys.exit(0)
    except typer.Exit as e:
        sys.exit(e.exit_code)
    except Exception as e:
        logger.exception(f"Error no manejado en CLI: {e}")
        console.print(f"\n[red]❌ Error crítico:[/] {str(e)[:200]}")
        console.print("[dim]Intenta 'pentia --help' para más información[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
