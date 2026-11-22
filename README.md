# PracaMagisterskaGarmin

Lokalny projekt analizy danych Garmin. Wyznacza deterministyczny wskaźnik PWS i przechowuje warianty asystowane jako wyniki porównawcze. Dashboard odczytuje opublikowaną migawkę przez lokalne API.

## Uruchamianie dashboardu

Z katalogu głównego uruchom backend:

```powershell
python -m pip install -r requirements.txt
python -m backend.api_server
```

W drugim terminalu uruchom frontend. Użyj wersji Node.js zgodnej z Angular 22, np. Node.js 24.15 lub nowszej z linii 24.x.

```powershell
cd frontend
npm ci
npm run dev
```

Dashboard jest dostępny pod adresem `http://127.0.0.1:5173`. Angular CLI przekazuje żądania `/api/v1` do FastAPI na porcie `8765`. Serwer ładuje migawkę z `data/published/dashboard_snapshots/current/`. Dane Garmin, migawki i poświadczenia przechowuj lokalnie. [Instrukcja frontendu](frontend/README.md)

## Struktura

- `data_gathering/` zawiera eksport Garmin, pozyskiwanie aktywności i odczyt workbooka.
- `data_processing/` zawiera normalizację i budowę cech dziennych.
- `algorithms/` zawiera obliczenia obciążenia, readiness, PWS i walidację propozycji wag.
- `backend/` zawiera lokalne API, obsługę migawek i kontrakty.
- `frontend/` zawiera dashboard Angular i wykresy Chart.js.
- `ai_prompts/` i `config/` zawierają instrukcje dla modeli i polityki obliczeń.
- `tests/` zawiera testy Pythona odpowiadające kontrolom opisanym w pracy. Testy Angulara uruchamia `npm test` w `frontend/`.
- `scripts/` zawiera skrypty uruchomieniowe, podglądy i pakowanie.
