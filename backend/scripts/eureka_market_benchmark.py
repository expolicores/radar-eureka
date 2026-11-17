"""Local private-price benchmark with bounded, optional Market Price Scout fallback."""

import argparse
import json
from pathlib import Path

from public_procurement.investigation.market_benchmark.diagnostics import rejected_diagnostic
from public_procurement.investigation.market_benchmark.foundry_scout import FoundryMarketPriceScout
from public_procurement.investigation.market_benchmark.page_verifier import HttpMarketPageVerifier
from public_procurement.investigation.market_benchmark.schemas import (
    ProductIdentity,
    PublicOffer,
    PublicProduct,
)
from public_procurement.investigation.market_benchmark.serpapi_adapter import SerpApiShoppingAdapter
from public_procurement.investigation.market_benchmark.serpapi_http import (
    SerpApiHttp,
    SerpApiSettings,
)
from public_procurement.investigation.market_benchmark.service import (
    MarketReportStore,
    run_benchmark,
)
from public_procurement.shared.config import Settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-product", type=Path)
    parser.add_argument("--brand")
    parser.add_argument("--model")
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument(
        "--diagnose-rejected",
        action="store_true",
        help="Include stored rejection fields in console output",
    )
    parser.add_argument(
        "--diagnose-receipt",
        type=Path,
        help="Diagnose an existing receipt offline; no providers or writes",
    )
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--source", choices=["auto", "serpapi", "mercadolibre"], default="auto")
    parser.add_argument(
        "--no-page-verification",
        action="store_true",
        help="Keep provider evidence without requesting retailer pages",
    )
    parser.add_argument(
        "--item-id", action="append", default=[], help="Concrete MCO listing ID; repeatable, max 10"
    )
    parser.add_argument(
        "--no-catalog", action="store_true", help="Only enrich concrete listing IDs"
    )
    parser.add_argument("--product-type")
    parser.add_argument("--size")
    parser.add_argument("--capacity")
    parser.add_argument("--product-family")
    parser.add_argument("--domain-id")
    parser.add_argument("--canonical-model")
    parser.add_argument("--no-scout", action="store_true", help="Disable optional agent fallback")
    parser.add_argument("--target-observations", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--max-observations", type=int, choices=range(1, 6), default=5)
    parser.add_argument(
        "--verbose", action="store_true", help="Print full JSON; receipt is always complete"
    )
    parser.add_argument(
        "--web-receipt",
        type=Path,
        help="Reuse existing web evidence at its original timestamp; original receipt is preserved",
    )
    args = parser.parse_args(argv)
    if args.diagnose_receipt:
        receipt = json.loads(args.diagnose_receipt.read_text(encoding="utf8"))
        print(json.dumps(rejected_diagnostic(receipt), ensure_ascii=True, indent=2))
        return
    if args.output_directory is None:
        parser.error("--output-directory is required for a new run")
    if (args.output_directory / "market_benchmark.json").exists():
        parser.error("Output receipt already exists; choose a new --output-directory")
    product: ProductIdentity
    if args.public_product:
        data = json.loads(args.public_product.read_text(encoding="utf8"))
        product = (
            PublicOffer if data.get("public_price_stage") == "offer" else PublicProduct
        ).model_validate(data)
    elif args.brand and args.model:
        product = ProductIdentity(brand=args.brand, model=args.model)
    else:
        parser.error("Usa --public-product o --brand y --model; sin evidencia pública no hay señal")
    context = {
        key: value
        for key, value in {
            "product_type": args.product_type,
            "size": args.size,
            "capacity": args.capacity,
            "product_family": args.product_family,
            "expected_domain_id": args.domain_id,
            "canonical_model": args.canonical_model,
        }.items()
        if value is not None
    }
    product = product.model_copy(update=context)
    from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
        MercadoLibreAdapter,
        MercadoLibreHttp,
        MercadoLibreSettings,
    )

    if args.target_observations > args.max_observations:
        parser.error("--target-observations must not exceed --max-observations")
    adapter = (
        MercadoLibreAdapter(
            MercadoLibreHttp(MercadoLibreSettings()), enable_catalog=not args.no_catalog
        )
        if args.source != "serpapi"
        else None
    )
    receipt = json.loads(args.web_receipt.read_text(encoding="utf8")) if args.web_receipt else None
    report = run_benchmark(
        product,
        shopping=SerpApiShoppingAdapter(SerpApiHttp(SerpApiSettings()))
        if args.source != "mercadolibre"
        else None,
        marketplace_adapter=adapter,
        listing_ids=args.item_id,
        existing_receipt=receipt,
        scout=FoundryMarketPriceScout() if args.source == "auto" and not args.no_scout else None,
        page_verifier=None if args.no_page_verification else HttpMarketPageVerifier(),
        target_observations=args.target_observations,
        max_observations=args.max_observations,
    )
    args.output_directory.mkdir(parents=True, exist_ok=True)
    path = args.output_directory / "market_benchmark.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    if args.publish:
        MarketReportStore(Settings().local_storage_path.parent / "investigation").write(report)
    summary = {
        "output": str(path),
        "status": report.get("status"),
        "query": report["query"],
        "shopping_discovery": {
            k: v
            for k, v in report.get("shopping_discovery", {}).items()
            if k != "shopping_candidates"
        },
        "market_price_scout": report.get("market_price_scout"),
        "page_verification": report.get("page_verification"),
        "benchmark": {
            k: v for k, v in report["benchmark"].items() if k not in {"observations", "duplicates"}
        },
        "comparison": report["comparison"],
        "mercadolibre": {
            k: v
            for k, v in report.get("mercadolibre", {}).items()
            if k
            in {
                "source_status",
                "catalog_product_id",
                "catalog_selection_reason",
                "request_count",
                "errors",
                "warnings",
                "retries",
            }
        },
        "errors": report["errors"],
        "candidate_verification": [
            {
                k: row[k]
                for k in (
                    "market_product_title",
                    "url",
                    "price",
                    "page_type",
                    "match_level",
                    "match_reason",
                    "discovery_score",
                    "valid_for_benchmark",
                    "verification_status",
                    "price_evidence_level",
                    "extraction_method",
                    "rejection_reason",
                    "currency",
                    "currency_inferred",
                    "product_id",
                    "shipping",
                    "source",
                    "captured_at",
                )
            }
            for row in report["benchmark"]["observations"]
        ][:10],
    }
    console = report.copy() if args.verbose else summary
    if args.diagnose_rejected:
        console["rejection_diagnostic"] = rejected_diagnostic(report)
    print(json.dumps(console, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
