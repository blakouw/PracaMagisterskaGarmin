# PracaMagisterskaGarmin

Projekt analizy danych Garmin. Wyznacza deterministyczny wskaźnik PWS i przechowuje warianty asystowane jako wyniki porównawcze.

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

Dashboard jest dostępny pod adresem `http://127.0.0.1:5173`.
