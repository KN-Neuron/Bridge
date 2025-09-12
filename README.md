# Bridge

[![CI](https://github.com/KN-Neuron/Bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/KN-Neuron/Bridge/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/neuron-bridge.svg)](https://badge.fury.io/py/neuron-bridge)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

**Wersja: 0.1.0**

**Bridge** to biblioteka (SDK) i aplikacja wiersza poleceń w Pythonie, która tworzy ujednolicony interfejs do zbierania danych z różnych urządzeń EEG. Działa jako "most" między sprzętem a oprogramowaniem analitycznym.

## Główne Cechy

-   **Architektura Pluginów**: Łatwe dodawanie wsparcia dla nowych urządzeń.
-   **Podwójne Zastosowanie**: Działa jako biblioteka Pythona (SDK) lub samodzielny serwer WebSocket.
-   **Ujednolicone API**: Zapewnia jeden, spójny sposób komunikacji z każdym wspieranym urządzeniem.

## Instalacja

**Wymagania:** Python 3.11

1.  **Instalacja biblioteki:**
    ```bash
    # Podstawowe użycie jako SDK
    pip install neuron-bridge

    # Instalacja z funkcjonalnością serwera
    pip install "neuron-bridge[server]"
    ```

2.  **Instalacja sterowników urządzenia:**
    Biblioteka nie zawiera zastrzeżonych SDK producentów – należy je zainstalować manualnie.
    -   **BrainAccess:** [Strona producenta](https://www.brainaccess.ai/download/).

## Szybki Start

### Użycie jako Serwer

Serwer WebSocket automatycznie łączy się z pierwszym dostępnym urządzeniem EEG.

```bash
bridge-server --host localhost --port 50050
```
Klienty mogą łączyć się z `ws://localhost:50050` i wysyłać żądania w formacie JSON (`{"request": "get_device_info"}`).

### Użycie jako Biblioteka (SDK)

Klasa `EEGConnector` to główny punkt wejścia do interakcji z urządzeniem.

```python
from bridge.eeg import EEGConnector, init, close

# Inicjalizacja sterowników
init()

try:
    with EEGConnector() as device:
        info = device.get_device_data()
        print(f"Połączono z: {info.name}")

        # Akwizycja 5 sekund danych
        eeg_data = device.get_output(duration=5.0)
        print(f"Pobrano dane o kształcie: {eeg_data.shape}")

except RuntimeError as e:
    print(f"Błąd: {e}")

finally:
    # Zwolnienie zasobów
    close()
```

## Rozwój Projektu

### Konfiguracja Środowiska

1.  **Sklonuj repozytorium:** `git clone https://github.com/KN-Neuron/Bridge.git`
2.  **Stwórz i aktywuj środowisko:** `python -m venv .venv && source .venv/bin/activate`
3.  **Zainstaluj zależności:** `pip install -e ".[dev]"`
4.  **Zainstaluj hooki pre-commit:** `pre-commit install` (jednorazowo)

### Proces Pracy

Projekt wykorzystuje `pre-commit` do automatyzacji sprawdzania i formatowania kodu.

1.  Wprowadź zmiany w kodzie.
2.  Dodaj pliki do commita: `git add .`
3.  Wykonaj commit: `git commit -m "Opis zmian"`
    -   Narzędzia (`ruff`, `black`, `mypy`, `pytest`) uruchomią się automatycznie.
    -   Jeśli kod zostanie automatycznie sformatowany, commit zostanie przerwany. To celowe – przejrzyj zmiany, dodaj je ponownie (`git add .`) i ponów commit.

### Dodawanie Nowego Urządzenia

1.  **Stwórz nowy moduł** w `bridge/eeg/`.
2.  **Zaimplementuj klasę** dziedziczącą po `EEGDevice`.
3.  **Zarejestruj ją** w `bridge/eeg/config.py`.
4.  **Dodaj testy** w katalogu `tests/`.
