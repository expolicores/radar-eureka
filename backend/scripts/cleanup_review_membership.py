"""Offline DB audit/cleanup only. Never executes discovery, scoring, documents or OCR."""

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.review_cleanup import cleanup_plan, execute_cleanup
from public_procurement.eureka.review_repositories import ReviewRepository
from public_procurement.eureka.review_services import project
from public_procurement.eureka.services import build_human_review_service
from public_procurement.shared.config import Settings
from public_procurement.shared.database import create_db_engine


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    engine = create_db_engine(settings)
    sessions = sessionmaker(engine)
    service = build_human_review_service(sessions, settings)

    def rebuild():
        data = ReviewRepository(sessions).read()
        return cleanup_plan(data, project(data, service.metadata(), service.clock()))

    if args.apply:
        plan = json.loads(args.audit.read_text(encoding="utf-8"))
        result = execute_cleanup(sessions, plan, rebuild)
        result["after"] = rebuild()
        args.audit.with_name(args.audit.stem + "-result.json").write_text(
            json.dumps(result, default=str, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps({k: result[k] for k in ("deleted", "selection_hash")}))
        print(
            json.dumps(
                {
                    k: result["after"][k]
                    for k in ("before", "delete_count", "protected_count", "retained_reasons")
                }
            )
        )
    else:
        plan = rebuild()
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(
            json.dumps(plan, default=str, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    k: plan[k]
                    for k in (
                        "before",
                        "delete_count",
                        "keep_count",
                        "protected_count",
                        "expected_remaining",
                        "selection_hash",
                    )
                }
            )
        )
        print(str(args.audit.resolve()))
    engine.dispose()


if __name__ == "__main__":
    main()
