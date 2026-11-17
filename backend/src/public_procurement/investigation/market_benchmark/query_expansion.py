"""Bounded reference queries from optional product context; no brand/category registry."""

import re

from .schemas import ProductIdentity


def expanded_queries(product: ProductIdentity) -> list[str]:
    variants: list[list[str | None]] = [
        [product.brand, product.model],
        [product.brand, product.product_type, product.model],
        [product.brand, product.size or product.capacity or product.dimensions, product.model],
        [
            product.brand,
            product.size or product.capacity,
            product.product_family or (model_family(product) or product.model).upper(),
        ],
    ]
    queries = [
        " ".join(part.strip() for part in parts if part and part.strip()) for parts in variants
    ]
    return list(dict.fromkeys(re.sub(r"\s+", " ", query) for query in queries))[:4]


def model_family(product: ProductIdentity) -> str | None:
    if product.product_family:
        return product.product_family.casefold()
    # A split reference is considered only with an explicit numeric size supplied by caller.
    size = re.match(r"(\d+(?:[.,]\d+)?)", product.size or "")
    model = product.model.casefold()
    if size and model.startswith(size[1]) and len(model[len(size[1]) :]) >= 4:
        return model[len(size[1]) :]
    return None
