"""Input validation helpers for PENTIA.

Pure functions (no I/O) so they are easy to unit-test. They exist to stop
argument injection: a target starting with ``-`` must never reach an external
scanner binary as a flag, and unchecked user input must never become a
filename, URL or model name.

Design notes
------------
* Targets are internal-pentest targets, so private / link-local / loopback
  IPs are explicitly ALLOWED. Only credentials embedded in a URL and
  non-http(s) schemes are blocked (see :func:`validate_url`).
* ``validate_output_dir`` confines output to a chosen base directory
  (the current working directory by default) so ``..`` escapes are rejected.
"""
from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse

__all__ = [
    "validate_target",
    "validate_url",
    "validate_model_name",
    "validate_output_dir",
    "sanitize_filename",
]

MAX_TARGET_LEN = 255
MAX_URL_LEN = 2048
MAX_FILENAME_LEN = 200

# Anything that could break out of an argument list into a shell, or that
# lets a value smuggle extra tokens/flags into a command line.
_SHELL_METACHARS = set("; & | $ ` \n \r \t")
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_HOSTNAME_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_FILENAME_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _reject_metachars(value: str, what: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{what} no puede estar vacío")
    if value != value.strip():
        raise ValueError(f"{what} no debe tener espacios al inicio o al final")
    if value.startswith("-"):
        raise ValueError(f"{what} no debe empezar con '-'")
    for ch in value:
        if ch in _SHELL_METACHARS:
            raise ValueError(f"{what} contiene un carácter no permitido: {ch!r}")
    if any(ch.isspace() for ch in value):
        raise ValueError(f"{what} no debe contener espacios")


def _is_hostname(value: str) -> bool:
    """True for a syntactically valid DNS hostname (no trailing dot)."""
    if len(value) > 253 or value.endswith("."):
        return False
    return all(_HOSTNAME_LABEL_RE.match(label) for label in value.split("."))


def _is_ip_or_cidr(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        pass
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


def validate_target(target: str) -> str:
    """Validate and normalize a scan target.

    Accepts a hostname, an IPv4/IPv6 address, a CIDR network, or an
    ``http(s)://`` URL. Returns the normalized target (the URL unchanged
    apart from stripping, otherwise the host/network as given).

    Raises :class:`ValueError` for empty input, overlong input, a leading
    ``-`` (argument-injection attempt), shell metacharacters, whitespace,
    or anything that is not a hostname, IP, CIDR or http(s) URL.
    """
    if not isinstance(target, str):
        raise ValueError("El target debe ser texto")
    target = target.strip()
    if not target:
        raise ValueError("El target no puede estar vacío")
    if len(target) > MAX_TARGET_LEN:
        raise ValueError("El target es demasiado largo")
    _reject_metachars(target, "El target")

    lowered = target.lower()
    if lowered.startswith(("http://", "https://")):
        # A URL target: reuse the URL rules, then return it unchanged.
        return validate_url(target)

    if "/" in target:
        if _is_ip_or_cidr(target):
            return target
        raise ValueError("El target no es una red CIDR válida")
    if _is_ip_or_cidr(target) or _is_hostname(target):
        return target
    raise ValueError("El target no es un hostname, IP, CIDR o URL válido")


def validate_url(url: str) -> str:
    """Validate an http(s) URL.

    Only ``http``/``https`` schemes are allowed and the URL must not embed
    credentials (``user:pass@host``). Private, loopback and link-local hosts
    are ALLOWED on purpose: PENTIA is an internal pentest tool and its
    targets live on private networks. Returns the URL unchanged (stripped).
    """
    if not isinstance(url, str):
        raise ValueError("La URL debe ser texto")
    url = url.strip()
    if not url:
        raise ValueError("La URL no puede estar vacía")
    if len(url) > MAX_URL_LEN:
        raise ValueError("La URL es demasiado larga")
    _reject_metachars(url, "La URL")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Solo se permiten URLs http:// o https://")
    if parsed.username or parsed.password:
        raise ValueError("La URL no debe incluir credenciales")
    host = parsed.hostname
    if not host:
        raise ValueError("La URL debe incluir un host")
    if not (_is_ip_or_cidr(host) or _is_hostname(host)):
        raise ValueError("El host de la URL no es válido")
    return url


def validate_model_name(model: str) -> str:
    """Validate an Ollama model name against a strict allowlist.

    Allowed: starts with an alphanumeric character, then up to 63 chars of
    alphanumerics, ``.``, ``_``, ``:`` or ``-`` (e.g. ``qwen2.5-coder``,
    ``llama3.1:8b``). Anything else is rejected so the name can never be
    interpreted as extra CLI flags/arguments.
    """
    if not isinstance(model, str):
        raise ValueError("El nombre del modelo debe ser texto")
    model = model.strip()
    if not _MODEL_RE.match(model):
        raise ValueError(f"Nombre de modelo no válido: {model!r}")
    return model


def validate_output_dir(path: str | Path, base: str | Path | None = None) -> Path:
    """Resolve ``path`` and require it to stay inside ``base``.

    ``base`` defaults to the current working directory. Relative paths are
    resolved against the CWD. ``..`` escapes and absolute paths outside the
    base raise :class:`ValueError`. The directory is NOT created here.
    """
    if path is None or (isinstance(path, str) and not path.strip()):
        raise ValueError("El directorio de salida no puede estar vacío")
    base_path = Path(base).resolve() if base is not None else Path.cwd().resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(base_path)
    except ValueError:
        raise ValueError(
            f"El directorio de salida {resolved} está fuera del directorio permitido {base_path}"
        ) from None
    return resolved


def sanitize_filename(name: str) -> str:
    """Return a safe filename derived from ``name``.

    Strips directories, replaces every run of unsafe characters with ``_``,
    rejects empty results and ``.``/``..``, strips leading dots/dashes, and
    caps the length. Never returns a value that can traverse directories.
    """
    if not isinstance(name, str):
        raise ValueError("El nombre de archivo debe ser texto")
    # Drop any directory components first (also defeats "../" tricks).
    name = name.replace("\\", "/").rsplit("/", 1)[-1].strip()
    name = _FILENAME_UNSAFE_RE.sub("_", name)
    name = name.strip("._-")
    if not name or name in (".", ".."):
        raise ValueError("Nombre de archivo no válido")
    if len(name) > MAX_FILENAME_LEN:
        stem, _, suffix = name.rpartition(".")
        if stem and len(suffix) <= 10:
            name = stem[: MAX_FILENAME_LEN - len(suffix) - 1] + "." + suffix
        else:
            name = name[:MAX_FILENAME_LEN]
    return name
