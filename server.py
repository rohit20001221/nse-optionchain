import asyncio
import json
from datetime import datetime
from http import HTTPStatus
from pathlib import Path

import websockets
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright.async_api import (
    Error as PlaywrightError,
)
from websockets.datastructures import Headers
from websockets.http11 import Request, Response

from greeks import calculate_gex
from utils import (
    extract_spot_price,
    get_days_to_expiry,
    option_chain_csv_js,
    option_chain_csv_to_json,
)

# Track connected HTML clients and cache the latest GEX payload
CONNECTED_CLIENTS: set[websockets.ServerConnection] = set()
LATEST_PAYLOAD: str | None = None
INDEX_HTML_PATH = Path(__file__).parent / "index.html"


def serve_http_request(
    connection: websockets.ServerConnection, request: Request
) -> Response | None:
    """Serve index.html for HTTP requests; let /ws upgrade to WebSocket."""
    if request.path == "/ws":
        return None

    if request.path in ("/", "/index.html"):
        if not INDEX_HTML_PATH.exists():
            return Response(
                HTTPStatus.NOT_FOUND,
                "Not Found",
                Headers([("Content-Type", "text/plain")]),
                b"index.html not found",
            )
        return Response(
            HTTPStatus.OK,
            "OK",
            Headers([("Content-Type", "text/html; charset=utf-8")]),
            INDEX_HTML_PATH.read_bytes(),
        )

    return Response(
        HTTPStatus.NOT_FOUND,
        "Not Found",
        Headers([("Content-Type", "text/plain")]),
        b"Not Found",
    )


async def broadcast(message: str) -> None:
    """Send the latest GEX JSON string to all connected HTML dashboards."""
    global LATEST_PAYLOAD
    LATEST_PAYLOAD = message

    if not CONNECTED_CLIENTS:
        return

    # Broadcast concurrently and drop any disconnected clients automatically
    websockets.broadcast(CONNECTED_CLIENTS, message)


async def ws_client_handler(websocket: websockets.ServerConnection) -> None:
    """Handle incoming browser dashboard WebSocket connections."""
    CONNECTED_CLIENTS.add(websocket)
    print(f"Dashboard connected ({len(CONNECTED_CLIENTS)} active)")
    try:
        # Immediately send the latest snapshot so the UI isn't blank on load
        if LATEST_PAYLOAD:
            await websocket.send(LATEST_PAYLOAD)

        # Keep connection open until the browser tab closes
        await websocket.wait_closed()
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        print(f"Dashboard disconnected ({len(CONNECTED_CLIENTS)} active)")


def create_websocket_handler(page: Page, context: BrowserContext, browser: Browser):
    async def handle_data(_payload=None):
        if page.is_closed():
            return

        spot_text = await page.locator("#equity_underlyingVal").inner_text(timeout=3000)
        spot_price = extract_spot_price(spot_text)

        expiry_date = await page.locator("#expirySelect").input_value(timeout=3000)
        days_to_expiry = get_days_to_expiry(expiry_date)

        raw_csv = await page.evaluate(option_chain_csv_js, "optionChainTable-indices")
        data = option_chain_csv_to_json(raw_csv)

        if spot_price and data:
            gex_report = calculate_gex(
                days_to_expiry=days_to_expiry,
                lot_size=75,
                option_chain=data,
                spot_price=spot_price,
            )
            gex_report["expiry_date"] = expiry_date
            gex_report["updated_at"] = datetime.now().strftime("%H:%M:%S")

            await broadcast(json.dumps(gex_report))

    async def on_websocket(ws):
        await asyncio.sleep(2)
        await handle_data()
        # Fixed typo: 'framereceived'
        ws.on("framereceived", handle_data)

    return on_websocket


async def run_scraper(playwright: Playwright) -> None:
    browser = await playwright.firefox.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    page.on("websocket", create_websocket_handler(page, context, browser))

    try:
        await page.goto(
            "https://www.nseindia.in/option-chain", wait_until="domcontentloaded"
        )
        await page.locator("#stream-optionchain-tile").check()
        await page.wait_for_event("close", timeout=0)
    except PlaywrightError as e:
        print(f"Playwright error: {e}")
    finally:
        for resource in (context, browser):
            await resource.close()


async def main() -> None:
    async with websockets.serve(
        ws_client_handler,
        "0.0.0.0",
        3001,
        process_request=serve_http_request,
    ):
        print("GEX WebSocket server running at http://localhost:3001")
        async with async_playwright() as playwright:
            await run_scraper(playwright)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")
