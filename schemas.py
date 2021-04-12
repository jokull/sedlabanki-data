from typing import Optional, List, Tuple, Dict
from pydantic import BaseModel


BASE_URL = (
    "https://www.sedlabanki.is/library/Fylgiskjol/Hagtolur/Fjarmalafyrirtaeki/{year}/"
)


class Row(BaseModel):
    institute: str
    category: Optional[str]
    row: int
    sector: str
    industry: Optional[str]


class Sheet(BaseModel):
    sheet: int = 0
    from_: int
    dates_row: int
    rows: List[Row]


class Workbook(BaseModel):
    url: str
    sheets: Optional[List[Sheet]]


schemas: Tuple[Workbook, ...] = (
    # Bankakerfi
    Workbook.parse_obj(
        {
            "url": BASE_URL + "INN_Utlan_{month:02d}{year}.xlsx",
            "sheets": (
                {
                    "sheet": 5,
                    "from_": 3,
                    "dates_row": 9,
                    "rows": (
                        {
                            "institute": "bank",
                            "sector": "household",
                            "category": "indexed",
                            "row": 15,
                        },
                        {
                            "institute": "bank",
                            "sector": "household",
                            "category": "nonindexed",
                            "row": 18,
                        },
                        {
                            "institute": "bank",
                            "sector": "household",
                            "category": "foreign",
                            "row": 21,
                        },
                    ),
                },
                {
                    "sheet": 2,
                    "from_": 3,
                    "dates_row": 9,
                    "rows": (
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "agriculture",
                            "row": 13,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "fisheries",
                            "row": 14,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "manufacturing",
                            "row": 15,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "utilities",
                            "row": 19,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "construction",
                            "row": 20,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "retail",
                            "row": 21,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "transport-and-communications",
                            "row": 22,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "services",
                            "row": 23,
                        },
                        {
                            "institute": "bank",
                            "sector": "business",
                            "industry": "other",
                            "row": 27,
                        },
                    ),
                },
            ),
        }
    ),
    # Lánasjóðir ríkisins
    Workbook.parse_obj(
        {
            "url": BASE_URL + "LSJ_Utlan%20e%20geirum_{year}M{month}.xlsx",
            "sheets": (
                {
                    "from_": 2,
                    "dates_row": 9,
                    "rows": (
                        {
                            "institute": "other",
                            "sector": "household",
                            "category": "indexed",
                            "row": 27,
                        },
                    ),
                },
            ),
        }
    ),
    Workbook.parse_obj(
        {"url": BASE_URL + "LSJ_Utlan%20e%20tegund_{year}M{month}.xlsx"}
    ),
    # Lífeyrissjóðir
    Workbook.parse_obj(
        {
            "url": BASE_URL + "LIF_Utlan%20e%20geirum_{year}M{month}.xlsx",
            "sheets": (
                {
                    "from_": 2,
                    "dates_row": 9,
                    "rows": (
                        {
                            "institute": "pension",
                            "sector": "household",
                            "category": "indexed",
                            "row": 27,
                        },
                        {
                            "institute": "pension",
                            "sector": "household",
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
)