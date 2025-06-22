# This is the repository of the WattWise Spezialveranstaltung Project 2024

## Vorwort von Betreuer

We provide some initial files for a quick start, which in large parts are based on the Agri-PV Plant Optimization project by Joshua Spreng.

*The project is structured as follows*
- The main.py file is the entry point of the program and contains the main functions to run the optimization process.
- src/util contains utility functions for retrieving data from Entso-e and Renewables.ninja

*for executing the code you need working API keys for Renewables.ninja and Entso-e. Also install the requirements by calling pip install -r requirements.txt*.  
If you use additional packages please add that to the requirements file

# Projektstruktur: WattWise Dash App

## Features
- Upload individueller Verbrauchsdaten.
- PV-Ertragsberechnung via API oder CSV
- Monte-Carlo-Lastprofil-Simulation
- Dynamische vs. statische Preisvergleiche eines Lastprofils. Wenn später  bessere Modelle gefunden werden, diese leicht eintauschbar.
- Interaktive Amortisationsanalyse #TODO


## Einstiegspunkt

- **`app.py`**  
  → Startpunkt der App  
  → Initialisiert die Dash-App, definiert Layout und Navigation  
  → Die App läuft dann unter: http://127.0.0.1:8050/ 
  → Enthält `dcc.Store` zur Zwischenspeicherung der Nutzer- und Modell-Daten


## Zentrale Logik

- **`controller.py`**  
  → Zentrale Callback-Logik  
  → Datei-Upload, Validierung und Modellstart per Button  
  → Speichert Ergebnisse im Dash-Store

- **`model.py`**  
  → Kern-Logik der Anwendung  
  → Funktionen zur Datenaufbereitung, Forecast, PV-Ertrags- & Preisberechnung  
  → Führt gesamte Modell-Pipeline aus

- **`wattWiseApp/pages/`** 
  Siehe unten


### Seiten (Views)

Unter `wattWiseApp/pages/`:

- **`home.py`**  
  → Seite zur Dateneingabe (z. B. Upload CSV, Standort, PV-Konfiguration)

- **`savings.py`**  
  → Seite zur Auswertung möglicher Ersparnisse  
  → Holt Daten aus dem Store und zeigt Simulationsergebnisse, interaktiv
  → <span style="color:red">Gerne hier weitere Plots etc. einfügen.</span>  
  → <span style="color:red">Auch Logik mit Amortisationsdauer noch nicht optimal.</span>  

- **`details.py`**  
  → Detaillierte Visualisierungen und Auswertungen (z. B. Lastprofile, Forecast-Vergleiche)
  → <span style="color:red">Hier ist Plazt, um sich auszutoben!</span>


### Hilfsfunktionen / Module
diese wurden auch zur Modell Evaluierumg benutzt.

- **`pv_prediction.py`**  
  → Solar-Ertragsprognose via API (z. B. Renewables Ninja) oder CSV

- **`montecarlo.py`**  
  → Lastprofil-Simulation per Monte Carlo  
  → Basis für Verbrauchsprognosen

- **`plots.py`**  
  → Generierung von Visualisierungen (z. B. Verbrauchsprofile, Vergleichsplots). <span style="color:red"> Allerdings erhalte ich hier noch ERRORs.</span>


### Daten & Cache

- **`data/`**  
  → Ablage externer Rohdaten (Strompreise, Standardlastprofile, Wetterdaten)

- **`simulations_cache/`**  
  → Ablage vorab berechneter Simulationsergebnisse als `.pkl` (zur Laufzeitbeschleunigung), diese dienten v.a. der Modellevaluierumg


### Hinweise

- **`secrets.json`**  
  → API-Zugänge und Token (z. B. für Entsoe oder Renewables Ninja)  
  → Wird per `.gitignore` ignoriert – **niemals committen!**


## Code Anwendung

### App: Verbrauchsprofil hochladen
Damit der Stromverbrauch korrekt verarbeitet werden kann, muss die hochgeladene CSV-Datei folgende Struktur erfüllen:

| Spalte        | Inhalt                              | Format / Beispiel                       |
|---------------|-------------------------------------|-----------------------------------------|
| `Time`        | Zeitstempel (stündlich)             | `2019-01-01 00:00`                      |
| `<Spaltenname>` | Stromverbrauch je Stunde (in kWh) | z. B. `0.24`                            |

**Wichtig**:  
 - Die Datei muss **stündliche Werte** enthalten
 - ie Spalte mit Verbrauchswerten kann beliebig benannt sein (z. B. `SFH3_P_TOT`, `Last`, `Haushalt_1`) – dieser Name muss im Formular explizit angegeben werden unter Name.

 Beispiel – Struktur einer gültigen CSV-Datei:

```csv
Time,SFH3_P_TOT
2019-01-01 00:00,0.24
2019-01-01 01:00,0.20
2019-01-01 02:00,0.22
...

