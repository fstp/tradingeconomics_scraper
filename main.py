import asyncio
import datetime
import itertools
from typing import Any, Dict, NoReturn

import httpx
import socketio
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.table import Table

import decrypt

headers = {
    "Host": "live.tradingeconomics.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": "https://tradingeconomics.com",
    "Connection": "keep-alive",
    "Referer": "https://tradingeconomics.com/",
    "Cookie": "_ga_SZ14JCTXWQ=GS2.1.s1777365737$o5$g1$t1777365766$j31$l0$h0; _ga=GA1.1.610154921.1776951954;AWSALB=iAu4rfE47QQ3vu12Au4vjisioZkH83+1pb3vUdF88F/Y2Eph6FtCJowIwMw9GLsViD7X9g89bOw1d47DoyCHbXy6oH18TrEivVe3vhE3px2xDuEALe91ivqEYQFE;AWSALBCORS=iAu4rfE47QQ3vu12Au4vjisioZkH83+1pb3vUdF88F/Y2Eph6FtCJowIwMw9GLsViD7X9g89bOw1d47DoyCHbXy6oH18TrEivVe3vhE3px2xDuEALe91ivqEYQFE;im_sharedid=af057a05-b2b2-491a-b73e-143fea017568; im_sharedid_cst=znv0HA%3D%3D;FCCDCF=%5Bnull%2Cnull%2Cnull%2C%5B%22CQjHcoAQjHcoAEsACBENCbFoAP_gAEPgACiQK3oB_C7EbCFCiDJ3IKMEMAhHgBBAYsAwAAYBAwAADBIQIBQCgkEYBAyAFCACCAAAKASBAAAgCAAAAUAAIAAFAABEAAwAIBAIIAAAgAAAAEAIAAAACIAAEQCAAAIEAEAAkAgAAAIASEAAAAAAAACBAAAAABAAAAAAAAAABAEAAQAAQAAAAAAAiAAAAAAAABAIAAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAABAAAAAAAQgsIgH8LsRsIUKIMFcgowQwCFeAEABiwDAABgEDAAAMEhAgBAKSQRIECIAQIAAIAAAgBAEAACgICAAAQAAAABUAAEQADAAgEAgAQACAAABAQAAAAAAIgAARAIAAAgQAQACACAAAAgBIQAAAAAAAAIEAAAAAEAAAAAAAAAAAAQAAIADAAAAAAACIAAAAAAAAEAgQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAQAA.ILCIB_C7EbCFCiDJ3IKMEMAhXgBBAYsAwAAYBAwAADBIQIBQCkkEaBAyAFCACCAAAKASBAAAoCAgAAUAAIAAVAABEAAwAIBAIIEAAgAAAQEAIAAAACIAAEQCAAAIEAEAAkAgAAAIASEAAAAAAAACBAAAAABAAAAAAAAAABAEAASAAwAAAAAAAiAAAAAAAABAIEAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAABAAAAAAAQgAAE%22%2C%222~61.89.122.161.184.196.230.314.385.442.445.494.550.576.827.1029.1033.1046.1047.1051.1067.1097.1126.1166.1301.1329.1342.1415.1516.1616.1725.1735.1765.1782.1917.1942.1958.1985.1987.2068.2072.2074.2107.2213.2219.2223.2224.2328.2331.2416.2501.2567.2568.2575.2657.2686.2778.2869.2878.2898.2908.2920.2963.3005.3023.3126.3234.3235.3253.3309.3731.6931.8931.13731.15731.33931~dv.%22%2C%2232351499-4C71-48A8-A145-9996D5580AE4%22%5D%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%220fea8e7e-9fab-4b60-8960-abca6054172c%5C%22%2C%5B1776951960%2C418000000%5D%5D%22%5D%5D%5D;__gads=ID=5b1e8ea853cc3256:T=1776951962:RT=1777365741:S=ALNI_MajW9JXCxWYpzmUXgKhQt_LAkWm8g;__gpi=UID=000013a6224a8953:T=1776951962:RT=1777365741:S=ALNI_MZwOSLx8R7Faz6OCPZBKtaELvFfaQ;__eoi=ID=6706d489d2451dd8:T=1776951962:RT=1777365741:S=AA-AfjaJhZKlsQAyVBCZR_n_7DB5;FCNEC=%5B%5B%22AKsRol8wEn747ooszsLUZNO7X1hmDVcUIgfb1vp20BkgvtP7B4wfxLEBJmgMfBAR1bpAX8Isb2ZN-LrxEgIUtpWVFE8zuST7C5SWnrPtVbcxFnsi0dEVnb1SweCxDi7Hf4HT3sLGrSDztbHAcNNZuaH8Hb_31J4Zcg%3D%3D%22%5D%5D",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

url = "https://live.tradingeconomics.com/?key=sun&url=%2Fus100%3Aind"
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


@sio.on("tick")  # type: ignore
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
