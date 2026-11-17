"""Explicit HTTP-page fixtures for pre-existing benchmark orchestration tests."""

import json
from typing import Any

from public_procurement.investigation.market_benchmark import service
from public_procurement.investigation.market_benchmark.page_verifier import (
    HttpMarketPageVerifier,
    PageResponse,
)


class FixturePageVerifier:
    def verify(self, product, candidate):
        # The old search fixture is also published as a synthetic retailer product page.
        # Tests of weak snippets call the real service without this explicit page fixture.
        data = {
            "@type": "Product",
            "name": candidate.market_product_title,
            "offers": {
                "@type": "Offer",
                "price": str(candidate.price or ""),
                "priceCurrency": "COP",
            },
        }
        body = ('<script type="application/ld+json">' + json.dumps(data) + "</script>").encode()
        verifier = HttpMarketPageVerifier(
            lambda url: PageResponse(url, 200, body, {"content-type": "text/html"})
        )
        return verifier.verify(product, candidate)


def verified_benchmark(*args: Any, **kwargs: Any):
    kwargs.setdefault("page_verifier", FixturePageVerifier())
    return service.run_benchmark(*args, **kwargs)


def verified_mercadolibre_benchmark(*args: Any, **kwargs: Any):
    kwargs.setdefault("page_verifier", FixturePageVerifier())
    return service.run_mercadolibre_benchmark(*args, **kwargs)
