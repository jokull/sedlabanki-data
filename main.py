import datetime as dt
from io import BytesIO
from typing import List, Optional, Dict, Tuple
import sqlite3

from pydantic import BaseModel
import ics
import openpyxl
import requests


DBNAME = "housing.db"


def create_db(path=DBNAME):
    dbconn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

    create_table_sql = """
    CREATE TABLE mortgages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE,
        institute VARCHAR,
        category VARCHAR,
        value INTEGER
    );
    """

    dbconn.cursor().execute(create_table_sql)

    return dbconn


SEDLABANKI_ICS_URL = "https://www.sedlabanki.is/library/Fylgiskjol/Hagtolur/Birtingar_2021%20Calendar.ics"
EVENTS = dict(
    (name, []) for name in ("Bankakerfi", "Önnur fjármálafyrirtæki", "Lífeyrissjóðir")
)

BASE_URL = (
    "https://www.sedlabanki.is/library/Fylgiskjol/Hagtolur/Fjarmalafyrirtaeki/{year}/"
)


class Row(BaseModel):
    institute: str
    category: Optional[str]
    row: int


class Sheet(BaseModel):
    sheet: int = 0
    from_: int
    dates_row: int
    rows: List[Row]


class Workbook(BaseModel):
    url: str
    sheets: Optional[List[Sheet]]


EXCEL_URLS: Dict[str, Tuple[Workbook, ...]] = {
    "Bankakerfi": (
        Workbook.parse_obj(
            {
                "url": BASE_URL + "INN_Utlan_{month:02d}{year}.xlsx",
                "sheets": (
                    {
                        "sheet": 5,
                        "from_": 3,
                        "dates_row": 9,
                        "rows": (
                            {"institute": "bank", "category": "indexed", "row": 15},
                            {"institute": "bank", "category": "nonindexed", "row": 18},
                            {"institute": "bank", "category": "foreign", "row": 21},
                        ),
                    },
                ),
            }
        ),
    ),
    "Önnur fjármálafyrirtæki": (
        Workbook.parse_obj(
            {
                "url": BASE_URL + "YFT_Utlan%20e%20geirum_{year}M{month:02d}.xlsx",
                "sheets": (
                    {
                        "from_": 2,
                        "dates_row": 9,
                        "rows": ({"institute": "other", "row": 27},),
                    },
                ),
            }
        ),
        Workbook.parse_obj(
            {"url": BASE_URL + "YFT_Utlan%20e%20tegund_{year}M{month:02d}.xlsx"}
        ),
    ),
    "Lífeyrissjóðir": (
        Workbook.parse_obj(
            {
                "url": BASE_URL + "LIF_Utlan%20e%20geirum_{year}M{month}.xlsx",
                "sheets": (
                    {
                        "from_": 2,
                        "dates_row": 9,
                        "rows": (
                            {"institute": "pension", "category": "indexed", "row": 27},
                            {
                                "institute": "pension",
                                "category": "nonindexed",
                                "row": 28,
                            },
                        ),
                    },
                ),
            },
        ),
        Workbook.parse_obj(
            {"url": BASE_URL + "LIF_Utlan%20e%20tegund_{year}M{month}.xlsx"}
        ),
    ),
}


def get_series(date, name):
    series = []
    for wb_model in EXCEL_URLS[name]:
        if wb_model.sheets is None:
            continue
        url = wb_model.url.format(year=date.year, month=date.month)
        response = requests.get(url)
        if response.status_code == 404:
            return None
        wb = openpyxl.load_workbook(BytesIO(response.content), data_only=True)
        for sheet_model in wb_model.sheets:
            sheet = wb.worksheets[sheet_model.sheet]
            _series: List[Tuple[str, str, List]] = []
            month_values = [
                c.value
                for c in sheet[sheet_model.dates_row][
                    sheet_model.from_ : sheet.max_column
                ]
            ]

            for row in sheet_model.rows:
                cells = sheet[row.row][sheet_model.from_ : sheet.max_column]
                assert len(month_values) == len(cells)
                values: List = [
                    (int(c.value * 1_000_000) if c.value else None) for c in cells
                ]
                _series.append((row.institute, row.category, values))

            series.append(
                (
                    month_values,
                    _series,
                )
            )

    return series


def main():
    today = dt.date.today()
    response = requests.get(SEDLABANKI_ICS_URL)
    response.encoding = "utf-8"
    calendar = ics.Calendar(response.text)

    for event in calendar.timeline:
        if event.begin.date() > today:
            continue
        if event.name not in EVENTS:
            continue
        EVENTS[event.name].append(event.begin)

    dbconn = create_db()

    for name, events in EVENTS.items():
        latest = events[-1].shift(months=-1)
        while True:
            series = get_series(latest, name)
            if series:
                break
            else:
                latest = latest.shift(months=-1)

        print(name, "-", latest.humanize())
        for month_values, s in series:
            for institute, category, values in s:
                for date, value in zip(month_values, values):
                    dbconn.execute(
                        "INSERT INTO mortgages(institute, category, value, date) values (?, ?, ?, ?)",
                        (institute, category, value, date),
                    )
            print()
            dbconn.commit()


if __name__ == "__main__":
    main()
