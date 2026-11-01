"""Opt-in real Foundry spike. --help / --show-tool-schema never contact Azure or DB."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from public_procurement.agents.eureka_assistant.foundry_client import FoundryClient
from public_procurement.agents.eureka_assistant.schemas import (
    TOOL_SCHEMAS,
    FoundrySettings,
    SpikeError,
)
from public_procurement.agents.eureka_assistant.service import EurekaAssistant
from public_procurement.agents.eureka_assistant.tools import read_only_tool
from public_procurement.shared.config import Settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?")
    parser.add_argument("--show-tool-schema", action="store_true")
    parser.add_argument(
        "--agent-version", help="Usar una versión existente verificada, sin crear otra."
    )
    args = parser.parse_args()
    if args.show_tool_schema:
        print(json.dumps(TOOL_SCHEMAS, ensure_ascii=False, indent=2))
        return 0
    if not args.question:
        parser.error("Indica una pregunta.")
    # No SDK HTTP/body/token logging, including failures during credential discovery.
    for namespace in ("azure", "openai", "httpx", "httpx2", "httpcore", "httpcore2"):
        logging.getLogger(namespace).setLevel(logging.CRITICAL)
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        config, settings = FoundrySettings(), Settings()
        print("Pregunta: " + args.question)
        with (
            DefaultAzureCredential(exclude_interactive_browser_credential=True) as credential,
            AIProjectClient(
                endpoint=config.azure_foundry_project_endpoint,
                credential=credential,
                connection_timeout=10,
                read_timeout=config.eureka_foundry_timeout_seconds,
                retry_total=0,
            ) as project,
            project.get_openai_client(
                timeout=config.eureka_foundry_timeout_seconds, max_retries=0
            ) as openai,
            read_only_tool(settings) as tool,
        ):

            def emit(event: str, value: Any) -> None:
                print(event + ": " + json.dumps(value, ensure_ascii=False))

            result = EurekaAssistant(
                FoundryClient(project, openai, config, agent_version=args.agent_version), tool, emit
            ).ask(args.question)
            print("Respuesta final: " + result.answer)
        return 0
    except SpikeError as error:
        print(str(error), file=sys.stderr)
        return 2
    except ImportError:
        print('Falta el SDK: instala el extra "foundry" del backend.', file=sys.stderr)
        return 3
    except Exception:
        print(
            "No se pudo iniciar el spike. Revisa variables, az login y acceso a PostgreSQL. "
            "No se muestran detalles sensibles.",
            file=sys.stderr,
        )
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
