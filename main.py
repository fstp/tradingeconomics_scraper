import asyncio
import datetime
import itertools
from typing import Any, Dict, NoReturn

import httpx
import socketio
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

import decrypt

headers = {
    "Host": "live.tradingeconomics.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": "https://tradingeconomics.com",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Referer": "https://tradingeconomics.com/",
    "Cookie": "AWSALB=M9i/Ouy2UJgKBqF5jkhrK5rNJnzFUsptSlPcOPOFqxOQD60VmEl1BK5jejTf4/yUTlem2HbLEfjWzKRCjvTWnsRwHwOuRvoX37ts9N3g1WC1y5eV4gW6TfQFAgs7; AWSALBCORS=M9i/Ouy2UJgKBqF5jkhrK5rNJnzFUsptSlPcOPOFqxOQD60VmEl1BK5jejTf4/yUTlem2HbLEfjWzKRCjvTWnsRwHwOuRvoX37ts9N3g1WC1y5eV4gW6TfQFAgs7",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "TE": "trailers",
}

url = "https://live.tradingeconomics.com/socket.io/?key=rain&url=%2Fsweden%2Fstock-market&t=POQpB1c"
sio = socketio.AsyncClient()
console = Console()
state: Dict[str, Dict[str, Any]] = {}
symbols_to_subscribe = [
    "spx:ind",
    "us100:ind",
    "btcusd:cur",
    "ukx:ind",
    "dax:ind",
    "s30:ind",
    "xauusd:cur",
    "usdsek:cur",
    "nky:ind",
    "vix:ind",
]
symbols_to_names = {
    "SPX:IND": "S&P 500",
    "US100:IND": "Nasdaq 100",
    "BTCUSD:CUR": "Bitcoin",
    "UKX:IND": "UK",
    "DAX:IND": "Germany",
    "S30:IND": "Stockholm",
    "XAUUSD:CUR": "Gold",
    "USDSEK:CUR": "Usd/Sek",
    "NKY:IND": "Nikkei",
    "VIX:IND": "VIX Index",
    "short_vix": "Short VIX",
}
persistent_state: Dict[str, Dict[str, Any]] = {}
# iChart-bodyLabels-cnt


def timestamp_to_datetime(ts: float) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(ts / 1000).replace(microsecond=0)


@sio.event
async def connect() -> None:
    console.print("[green]Connected to server[/]")
    console.print(f"My sid is [bold]{sio.sid}[/]")
    await sio.emit("subscribe", {"s": symbols_to_subscribe})


@sio.event
async def disconnect():
    console.print("[red]Disconnected from server[/]")


@sio.on("tick")  # type:ignore
async def handle_tick(data: bytes) -> None:
    """
    Event handler for the "tick" event.

    This function is triggered whenever a "tick" event is received. It processes the incoming data,
    decrypts it, converts the timestamps to human-readable datetime format, and updates the global state.

    Args:
        data (bytes): The encrypted binary message received from the "tick" event.
    """
    global state
    decrypted_data = decrypt.decrypt_binary_message(data)
    decrypted_data["dt"] = timestamp_to_datetime(decrypted_data["dt"])
    decrypted_data["odt"] = timestamp_to_datetime(decrypted_data["odt"])
    state[decrypted_data["s"]] = decrypted_data
    update_persistent_state(symbol=decrypted_data["s"], pch=decrypted_data["pch"])


def create_layout() -> Layout:
    """
    Create and return a root layout with two split rows.

    The root layout is split into two sub-layouts: 'left' and 'right'.

    Returns:
        Layout: The root layout with 'left' and 'right' sub-layouts.
    """
    layout = Layout(name="root")
    layout["root"].split_column(
        Layout(name="0"),
        Layout(name="1"),
        Layout(name="2"),
        Layout(name="3"),
        Layout(name="4"),
    )
    layout["root"]["0"].split_row(
        Layout(name="00"), Layout(name="01"), Layout(name="02")
    )
    layout["root"]["1"].split_row(
        Layout(name="10"), Layout(name="11"), Layout(name="12")
    )
    layout["root"]["2"].split_row(
        Layout(name="20"), Layout(name="21"), Layout(name="22")
    )
    layout["root"]["3"].split_row(Layout(name="30"), Layout(name="31"))
    layout["root"]["4"].split_row(
        Layout(name="40"), Layout(name="41"), Layout(name="42")
    )
    return layout


def format_pch(pch: float) -> str:
    """
    Format the percentage change (pch) value with color coding.

    Args:
        pch (float): The percentage change value to be formatted.

    Returns:
        str: The formatted percentage change value wrapped in color tags.
             If the value is non-negative, it is wrapped in green color tags.
             If the value is negative, it is wrapped in red color tags.
    """
    if pch >= 0.0:
        return f"[green]{pch}%[/]"
    else:
        return f"[red]{pch}%[/]"


def create_table(symbol: str, width=30) -> Table:
    """
    Create a table with symbol data.

    This function creates a table with two columns: 'Key' and 'Value'.
    It populates the table with key-value pairs which contains all
    received symbol data.

    Args:
        symbol (str): Symbol to display.

    Returns:
        Table: A table object populated with the symbol data.
    """
    if symbol in state:
        title = symbols_to_names[symbol]
        table = Table(title=title)

        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        for key, value in state[symbol].items():
            if key == "pch":
                value = format_pch(value)
            table.add_row(key, str(value))

        for key, value in persistent_state.get(symbol, {}).items():
            if key == "max_pch" or key == "min_pch":
                value = format_pch(value)
            table.add_row(key, str(value))

        table.width = width
        return table

    # If no symbol data is found
    return Table(title=symbol)


async def background():
    global console
    layout = create_layout()
    with Live(layout, console=console, screen=True, auto_refresh=False) as live:
        while True:
            size = 35
            height = 16
            layout["0"].size = height
            layout["0"]["00"].size = size
            layout["0"]["01"].size = size
            layout["0"]["02"].size = size
            layout["0"]["00"].update(create_table("SPX:IND", width=size))
            layout["0"]["01"].update(create_table("US100:IND", width=size))
            layout["0"]["02"].update(create_table("BTCUSD:CUR", width=size))

            layout["1"].size = height
            layout["1"]["10"].size = size
            layout["1"]["11"].size = size
            layout["1"]["12"].size = size
            layout["1"]["10"].update(create_table("UKX:IND", width=size))
            layout["1"]["11"].update(create_table("DAX:IND", width=size))
            layout["1"]["12"].update(create_table("S30:IND", width=size))

            layout["2"].size = height
            layout["2"]["20"].size = size
            layout["2"]["21"].size = size
            layout["2"]["22"].size = size
            layout["2"]["20"].update(create_table("XAUUSD:CUR", width=size))
            layout["2"]["21"].update(create_table("USDSEK:CUR", width=size))
            layout["2"]["22"].update(create_table("NKY:IND", width=size))

            layout["3"].size = height
            layout["3"]["30"].size = size
            layout["3"]["31"].size = size
            layout["3"]["30"].update(create_table("VIX:IND", width=size))
            layout["3"]["31"].update(create_table("short_vix", width=size))

            layout["4"].size = height
            layout["4"]["40"].size = size
            layout["4"]["41"].size = size
            layout["4"]["42"].size = size
            layout["4"]["40"].update(create_table("VIX Term Apr", width=size))
            layout["4"]["41"].update(create_table("VIX Term May", width=size))
            layout["4"]["42"].update(create_table("VIX Term Jun", width=size))

            live.update(layout, refresh=True)
            await asyncio.sleep(0.2)


async def fetch_shortvix_data() -> NoReturn:
    """
    Fetch the latest Mini Short VIX information from BNP Paribas.

    Process the response to extract the previous day's close price, the latest
    timestamp, and the latest price. Calculates the net change (nch) and percentage change (pch)
    from the previous day's close price and updates the global state with this information.

    This function runs in an infinite loop, fetching and updating the data every 30 seconds.
    """
    global state
    url = "https://www.educatedtrading.bnpparibas.se/getchartdata.ashx"
    params = {
        "currentCulture": "sv-SE",
        "instrument": "NLBNPSE11U10",  # Mini Short VIX BNP88
        "chartPeriod": "Intraday",
        "chartType": "area",
        "exchange": "BNP",
        "underlyingId": "17790",
        "underlyingExchange": "0000070880",
    }

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                open = data["previousDayClose"]
                price_series = data["series"][0]["data"]

                if not price_series:
                    state["short_vix"] = {
                        "closing_price": open,
                        "state": "closed",
                    }
                    continue

                dt = timestamp_to_datetime(price_series[-1]["x"])
                price = price_series[-1]["y"]
                nch = round(price - open, 2)
                pch = round((price - open) / open * 100, 2)
                update_persistent_state(symbol="short_vix", pch=pch)
                state["short_vix"] = {"p": price, "nch": nch, "pch": pch, "dt": dt}
            await asyncio.sleep(30)


def update_persistent_state(symbol: str, pch: float) -> None:
    """
    If symbol is in persistent state then set min_pch and max_pch
    """
    global persistent_state

    if symbol in persistent_state:
        if pch > persistent_state[symbol]["max_pch"]:
            persistent_state[symbol]["max_pch"] = pch
        if pch < persistent_state[symbol]["min_pch"]:
            persistent_state[symbol]["min_pch"] = pch
    else:
        persistent_state[symbol] = {"max_pch": pch, "min_pch": pch}


async def fetch_vix_term_structure() -> NoReturn:
    global state
    url = "http://vixcentral.com/ajax_update?_=1731660722644"
    headers = {
        "Host": "vixcentral.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "X-Requested-With": "XMLHttpRequest",
        "DNT": "1",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "Referer": "http://vixcentral.com/",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                list1 = data[0]
                list2 = data[2]
                list3 = data[3]
                zipped_data = zip(list1, list2, list3)
                for name, current, previous in itertools.islice(zipped_data, 3):
                    if previous == 0.0:
                        previous = current
                    nch = round(current - previous, 2)
                    pch = round((current - previous) / previous * 100, 2)
                    dt = datetime.datetime.now().replace(microsecond=0)
                    name = f"VIX Term {name}"
                    symbols_to_names[name] = name
                    state[name] = {
                        "curr": current,
                        "prev": previous,
                        "nch": nch,
                        "pch": pch,
                        "dt": dt,
                    }
                    update_persistent_state(symbol=name, pch=pch)
                await asyncio.sleep(30)


async def main():
    try:
        await sio.connect(
            url=url,
            headers=headers,
        )
        task = sio.start_background_task(background)
        await asyncio.gather(
            sio.wait(), task, fetch_shortvix_data(), fetch_vix_term_structure()
        )
    except asyncio.CancelledError:
        await sio.disconnect()
        console.print("[red]Disconnected from server[/]")


if __name__ == "__main__":
    asyncio.run(main())
