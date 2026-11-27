"""SECOP I popup guard for a disposable context. No live provider entry point."""

import asyncio
from collections.abc import Callable
from pathlib import Path

from eureka_nacional_cdp_stream import CLOSE_TIMEOUT, RejectionError
from playwright.async_api import Error as PlaywrightError


class Secop1PopupGuard:
    def __init__(self, marker: Path):
        self.marker = marker
        self.native_downloads_denied = False
        self.context_closed = False
        self._owns_marker = False
        self.context = None
        self.control = None
        self.context_id = None
        self.source = None

    async def start(self, browser):
        # Reserve before constructing anything browser-side. An existing marker belongs
        # to another attempt and must never be removed by this guard.
        try:
            with self.marker.open("x", encoding="utf8") as lock:
                self._owns_marker = True
                lock.write("secop1-disposable-context\n")
        except FileExistsError:
            raise RejectionError("stream_close_unverified") from None

        self.control = await browser.new_browser_cdp_session()
        self.context = await browser.new_context(accept_downloads=False)
        self.source = await self.context.new_page()
        source_cdp = await self.context.new_cdp_session(self.source)
        info = (await source_cdp.send("Target.getTargetInfo"))["targetInfo"]
        ids = (await self.control.send("Target.getBrowserContexts"))["browserContextIds"]
        context_id = info.get("browserContextId")
        if not context_id or context_id not in ids:
            raise RejectionError("disposable_context_unverified")
        self.context_id = context_id
        await self.control.send(
            "Browser.setDownloadBehavior",
            {"behavior": "deny", "browserContextId": context_id, "eventsEnabled": True},
        )
        self.native_downloads_denied = True
        return self.source

    async def open_blank(self):
        if not self.native_downloads_denied or self.context_closed:
            raise RejectionError("native_download_guard_unavailable")
        # Open only a blank target. The caller submits the form only after preparation.
        async with asyncio.timeout(4):
            async with self.context.expect_page(timeout=3500) as popup:
                opened = await self.source.evaluate(
                    "() => window.open('about:blank', '_blank') !== null"
                )
                if not opened:
                    raise RejectionError("popup_blocked")
            return await popup.value

    async def prepare(self, popup, on_pause: Callable):
        async with asyncio.timeout(4):
            if (
                not self.native_downloads_denied
                or self.context_closed
                or popup.is_closed()
                or popup.context != self.context
                or popup.url != "about:blank"
                or await popup.opener() != self.source
                or not await popup.evaluate(
                    "() => origin !== 'null' && window.opener?.location.origin === origin"
                )
            ):
                raise RejectionError("popup_identity_unverified")
            cdp = await self.context.new_cdp_session(popup)
            info = (await cdp.send("Target.getTargetInfo"))["targetInfo"]
            if info.get("browserContextId") != self.context_id:
                raise RejectionError("popup_context_mismatch")
            frame = (await cdp.send("Page.getFrameTree"))["frameTree"]["frame"]["id"]
            cdp.on("Fetch.requestPaused", on_pause)
            await cdp.send(
                "Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]}
            )
            return cdp, frame

    async def close(self):
        if not self._owns_marker:
            return False
        if self.context is None:
            return False
        try:
            async with asyncio.timeout(CLOSE_TIMEOUT):
                await self.context.close()
                if self.control is None or self.context_id is None:
                    return False
                contexts = (await self.control.send("Target.getBrowserContexts"))[
                    "browserContextIds"
                ]
                targets = (await self.control.send("Target.getTargets"))["targetInfos"]
                self.context_closed = self.context_id not in contexts and not any(
                    target.get("browserContextId") == self.context_id for target in targets
                )
        except (TimeoutError, PlaywrightError):
            self.context_closed = False
        return self.context_closed

    def release_after_worker(self, *, worker_closed: bool):
        if self._owns_marker and self.context_closed and worker_closed is True:
            self.marker.unlink()
            self._owns_marker = False
            return True
        return False
