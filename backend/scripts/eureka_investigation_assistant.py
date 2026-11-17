"""Explain persisted investigation runs; no discovery, market requests or data writes."""

import argparse
import json
import logging
import sys
from uuid import UUID, uuid4

from public_procurement.agents.investigation_assistant import diagnostics
from public_procurement.agents.investigation_assistant.chat import InvestigationChat
from public_procurement.agents.investigation_assistant.service import (
    READERS,
    AssistantError,
    summary,
)
from public_procurement.shared.config import Settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "message", nargs="?", default="¿Qué encontró la última corrida investigativa?"
    )
    parser.add_argument("--run-id", type=UUID)
    parser.add_argument(
        "--diagnose", action="store_true", help="Safe Foundry stages and tool trace on stderr"
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Read DTOs and grounded summary offline; no Foundry request",
    )
    args = parser.parse_args(argv)
    handler = logging.StreamHandler(sys.stderr) if args.diagnose else None
    previous_level = diagnostics.logger.level
    if handler:
        diagnostics.logger.addHandler(handler)
        diagnostics.logger.setLevel(logging.INFO)
    try:
        chat = InvestigationChat(Settings())
        if args.snapshot:
            queries = chat.query(args.message, args.run_id)
            reads = (
                {
                    name: queries.dispatch(name, {"run_id": str(queries.run.run_id)})
                    for name in READERS
                }
                if queries.run
                else {}
            )
            print(
                json.dumps(
                    {
                        "mode": "offline_snapshot",
                        "run": queries.metadata(),
                        "tools": reads,
                        "response": summary(queries.metadata(), reads),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            reply = chat.chat(args.message, None, args.run_id, uuid4())
            print(reply.model_dump_json(indent=2))
        return 0
    except Exception as error:
        diagnostic = (
            error.diagnostic
            if isinstance(error, AssistantError)
            else diagnostics.failure("cli_or_local_read", error)
        )
        print(
            json.dumps(
                {
                    "code": error.code
                    if isinstance(error, AssistantError)
                    else "assistant_unavailable",
                    "diagnostic": diagnostic,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        print(
            "No fue posible consultar el asistente. "
            "Verifica configuración Foundry y resultados locales.",
            file=sys.stderr,
        )
        return 1
    finally:
        if handler:
            diagnostics.logger.removeHandler(handler)
            diagnostics.logger.setLevel(previous_level)
            handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
