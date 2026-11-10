# Security Policy

## Authorized use only

Pentia is a red-team / security-assessment tool. Use it **only against
systems you own or have explicit, written authorization to test**. Do not
use it against third-party systems, and do not use it to access, disrupt,
or exfiltrate data you are not authorized to handle.

## Reporting vulnerabilities

If you find a security vulnerability in Pentia itself, please report
it by email to **jesjuarez590@gmail.com** with the subject
**"Vulnerabilidad en PENTIA"**. Include in the report:

- The affected Pentia version (see `pentia version`).
- Steps to reproduce the vulnerability.
- The impact (what an attacker could do with it).

Do not publish the vulnerability, a proof of concept, or exploit
details before a fix is available. Reports are handled privately and
the reporter will be credited if they wish.

## No unauthenticated remote use

The web UI (`pentia serve`) has **no authentication**. By design it binds
to localhost only (`127.0.0.1`, port `8000` by default). Binding it to a
non-loopback address exposes unauthenticated scan and LLM endpoints to
the network — do not do so unless you fully understand the risk and have
placed the service behind your own authenticated, network-isolated
access control.

## Localhost-only by design

Scans, enrichment, and the local memory store are intended to run on
your own machine against authorized targets. Pentia does not provide
multi-user isolation: anyone who can reach a running instance can use it.

## Model files from trusted sources only

Pentia loads local model files (e.g. LightGBM/XGBoost/RandomForest
classifiers). Model files can execute code when deserialized, so only
load model files you trained yourself or obtained from a source you
trust. Never load a model file from an untrusted download, attachment,
or public share.
