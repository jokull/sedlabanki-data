# Seðlabanki Húsnæðisgögn

Seðlabankinn miðlar gögnum um útlán með veði í heimilum í Excel skjölum.

Þetta er kóði til að sækja sjálfvirkt nýjustu skjölin, pilla út réttar tímaraðir
og setja í SQLite grunn.

Til að smíða grunninn frá … grunni …

```bash
poetry install
rm housing.db
poetry run python main.py
poetry run datasette
```
