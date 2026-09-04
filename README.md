# Quality Dip Scanner

Ein lokaler Nasdaq-100-Scanner fuer die Frage: Welche Aktien sind ungewoehnlich stark gefallen, waehrend Qualitaet und Bewertung attraktiv bleiben?

## Start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
streamlit run app.py
```

Die App lädt das aktuelle Nasdaq-100-Universum vom Nasdaq-Endpunkt, historische Kurse über `yfinance` und Fundamentaldaten über die SEC CompanyFacts API. Für SEC-Zugriffe sollte `SEC_USER_AGENT` eine identifizierende Kontaktadresse enthalten:

```powershell
$env:SEC_USER_AGENT = "Stockscreener dein.name@example.com"
```

## Datenbank

Standardmaessig wird SQLite verwendet. Fuer PostgreSQL:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost/stockscreener"
pip install "psycopg[binary]"
```

## Architektur

- `stockscreener/models.py`: historisierte Unternehmen, Index-Mitgliedschaften, Preise, Financials und Signals
- `stockscreener/providers.py`: Nasdaq-, yfinance- und SEC-CompanyFacts-Provider
- `stockscreener/scoring.py`: technische Kennzahlen sowie Dip-, Quality- und Valuation-Score
- `stockscreener/pipeline.py`: Laden, Berechnen und Persistieren eines Scans
- `app.py`: Streamlit-Dashboard

SEC-CompanyFacts werden in `SecCompanyFactsProvider` geladen und für Wachstum, Margen, ROIC und FCF-Yield normalisiert. Nicht von der SEC gelieferte Vergleichskennzahlen werden neutral bewertet.

Die Bewertungsmetrik ist auf das Muster „Qualitätsunternehmen nach einem temporären Rückgang“ kalibriert: Mehrwöchige Kursverluste und der 52-Wochen-Drawdown zählen stärker als ein einzelner 5-Tage-Schock. Robuste operative Qualität (ROIC, FCF-Marge und operative Marge) wird höher gewichtet; Bewertung bleibt ein zusätzlicher, aber nicht zwingender Vorteil.
