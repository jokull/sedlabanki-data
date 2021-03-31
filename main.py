import datetime as dt
from io import BytesIO
from typing import List, Optional, Tuple
import sqlite3

import ics
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
import requests

from schemas import schemas, Row


DBNAME = "credit.db"


def create_db(path=DBNAME):
    dbconn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

    create_table_sql = """
    CREATE TABLE credit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE,
        institute VARCHAR,
        sector VARCHAR,
        industry VARCHAR,
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


def get_series(date, name):
    series = []
    for wb_model in schemas[name]:
        if wb_model.sheets is None:
            continue
        url = wb_model.url.format(year=date.year, month=date.month)
        response = requests.get(url)
        if response.status_code == 404:
            return None
        wb: openpyxl.Workbook = openpyxl.load_workbook(
            BytesIO(response.content), data_only=True
        )
        for sheet_model in wb_model.sheets:
            sheet: Worksheet = wb.worksheets[sheet_model.sheet]  # type: ignore
            _series: List[Tuple[Row, List[Optional[int]]]] = []
            month_values = [
                c.value
                for c in sheet[sheet_model.dates_row][
                    sheet_model.from_ : sheet.max_column
                ]
            ]

            for row in sheet_model.rows:
                cells = sheet[row.row][sheet_model.from_ : sheet.max_column]
                assert len(month_values) == len(cells)
                values: List[Optional[int]] = [
                    (int(c.value * 1_000_000) if c.value else None) for c in cells
                ]
                _series.append((row, values))

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
            for row, values in s:
                for date, value in zip(month_values, values):
                    dbconn.execute(
                        "INSERT INTO credit(institute, category, sector, industry, value, date) values (?, ?, ?, ?, ?, ?)",
                        (
                            row.institute,
                            row.category,
                            row.sector,
                            row.industry,
                            value,
                            date,
                        ),
                    )
            dbconn.commit()


if __name__ == "__main__":
    main()
