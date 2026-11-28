"""Passive profile preflight in a temporary tab of the dedicated Edge (no feed, no POST to SECOP).

Reuses PassivePreflight unchanged: the app's own feed requests are aborted before leaving the
browser and only categories and counts are returned, never identifiers. The habitual tab is
never touched and the browser is never closed; the temporary tab is closed at the end.
"""

import asyncio
import json

from eureka_nacional_secop1_acquire import (
    CDP,
    OFFICIAL_HOSTS,
    PAGE_STATE,
    PORT,
    PROFILE_DIR,
    PROVIDER_HOSTS,
    listener_info,
)
from eureka_nacional_secop1_preflight import (
    PassivePreflight,
    dedicated_browser_checks,
    is_provider,
)

from public_procurement.licitaciones_cdp.configuration import resolve_profile_id

CONTRACTS_URL = "https://col.licitaciones.info/cliente/contratos"
VERDICT_KEYS = (
    "session",
    "navigation",
    "feed",
    "profile",
    "profile_count",
    "profile_changed",
    "profile_source",
    "official_blocked",
    "inventory_blocked",
    "provider_errors",
    "reasons",
)


async def _check():
    from playwright.async_api import async_playwright

    out = {"feed_requests_forwarded": 0, "posts_forwarded": 0}
    ok, checks = dedicated_browser_checks(listener_info(), port=PORT, profile_dir=PROFILE_DIR)
    out["dedicated_browser"] = checks
    if not ok:
        out["result"] = "not_dedicated_browser"
        return out
    preflight = PassivePreflight(expected_profile_id=resolve_profile_id())
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(CDP, timeout=5000, no_defaults=True)
        contexts = [c for c in browser.contexts if any(is_provider(p.url) for p in c.pages)]
        if len(contexts) != 1:
            out["result"] = "session_context_missing_or_ambiguous"
            return out
        context = contexts[0]
        habitual = list(context.pages)
        page = await context.new_page()
        try:

            async def restrict(route):
                request = route.request
                body = (
                    request.post_data
                    if request.method == "POST" and is_provider(request.url)
                    else None
                )
                decision = preflight.observe_request(request.url, body)
                del body
                if decision != "allowed":
                    return await route.abort("blockedbyclient")
                if request.method == "POST":
                    out["posts_forwarded"] += 1
                return await route.continue_()

            def on_response(response):
                if response.frame.page is page and is_provider(response.url):
                    preflight.observe_response(
                        response.url,
                        method=response.request.method,
                        resource_type=response.request.resource_type,
                        status=response.status,
                        json="json" in response.headers.get("content-type", ""),
                    )

            await page.route(PROVIDER_HOSTS, restrict)
            await page.route(OFFICIAL_HOSTS, restrict)
            page.on("response", on_response)
            preflight.record_own_navigation(CONTRACTS_URL)
            try:
                await page.goto(CONTRACTS_URL, wait_until="domcontentloaded", timeout=20000)
            except Exception as error:
                out["navigation_error"] = type(error).__name__
            await page.wait_for_timeout(8000)
            async with asyncio.timeout(5):
                preflight.observe_page(await page.evaluate(PAGE_STATE))
            verdict = preflight.verdict()
            out["verdict"] = {key: verdict[key] for key in VERDICT_KEYS}
        finally:
            await page.close()
            out["habitual_pages_untouched"] = all(not p.is_closed() for p in habitual)
    return out


def passive_profile_check():
    return asyncio.run(_check())


if __name__ == "__main__":
    print(json.dumps(passive_profile_check(), ensure_ascii=False))
