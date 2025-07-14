# RADME.md
# This is the repository of the WattWise Spezialveranstaltung Project 2024

## Vorwort von Betreuer

We provide some initial files for a quick start, which in large parts are based on the Agri-PV Plant Optimization project by Joshua Spreng.

*The project is structured as follows*
- The main.py file is the entry point of the program and contains the main functions to run the optimization process.
- src/util contains utility functions for retrieving data from Entso-e and Renewables.ninja

*for executing the code you need working API keys for Renewables.ninja and Entso-e. Also install the requirements by calling pip install -r requirements.txt*.  
If you use additional packages please add that to the requirements file.

## Installationshinweis: 
Dieses Projekt benötigt zwei API-Keys:
- [Renewables.ninja](https://www.renewables.ninja/) API-Token
- [ENTSO-E Transparency](https://transparency.entsoe.eu/) API-Key

Erstelle deine eigene `secrets.json`:

```json
{
    "ninja_token": "DEIN_RENEWABLES_NINJA_TOKEN_HIER",
    "entsoe_api_key": "DEIN_ENTSOE_TOKEN_HIER"
}
```

Installiere auch `requirements.txt`:
```bash
pip install -r requirements.txt
```


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
```



# Projektstruktur: WattWise Haushaltslastprofil-Simulation & Prognosemodellierung

#### Dieses Projekt implementiert und vergleicht verschiedene Modelle zur Vorhersage des Stromverbrauchs einzelner Haushalte. Grundlage sind historische Verbrauchsdaten, Standardlastprofile (SLP), Wetterdaten (insbesondere PV-Erzeugung) sowie dynamische Strompreise. Die Modelle werden anhand realer Verbrauchsdaten bewertet und ermöglichen einen praxisnahen Vergleich verschiedener Prognoseansätze.


## Inhalt

### Überblick der Verbrauchsprognose-Modelle:

| Modell  | Kurzbeschreibung                                                                                                    |
|---------|---------------------------------------------------------------------------------------------------------------------|
| **A**   | **Monte-Carlo-Modell:** 100 zufällig erzeugte Jahreslastprofile auf Basis des 2-Wochen-Haushaltsprofils. Saisonale Faktoren aus dem SLP 2019 werden angewendet. Liefert eine Verteilung möglicher Verläufe inkl. Unsicherheiten. |
| **B1**  | **Customer-Wochen-Profil:** Einfaches Modell. Das mittlere Tagesprofil (werktags & Wochenende) der 2/4-Wochen-Daten wird auf das gesamte Jahr 2020 übertragen. |
| **B2**  | **Hybridmodell: Customer-Wochen + SLP kombiniert** Kombination aus B1 und SLP-Profil (Standardlastprofil 2019), gewichtet nach Saison. In saisonaler Hauptzeit überwiegt das 2/4-Wochen-Profil, außerhalb dominiert das SLP. |

### PV Balkon-Erzeugung integrieren
**Ziel:** Einbezug von Photovoltaikdaten in Haushaltsverbrauchsprognosen  
**Netto-Lastberechnung:** 
Der Stromverbrauch des Haushalts wird stündlich um die erzeugte PV-Leistung reduziert.  

**Formel:** 
$$
Nettoverbrauch = max(Verbrauch − PV-Erzeugung, 0)
$$




### Modellbewertung:
  - Normalized Mean Absolute Error (NMAE)
  - Stromkostenberechnung unter:
    - dynamischem Preis (z. B. Tibber, Entso-E Spotpreise)
    - mit & ohne PV-Eigenverbrauch

## Projektstruktur

```bash
.
├── main.py                       # Hauptskript zur Modellausführung
├── pv_prediction.py              # PV-Datenanbindung (API + Netto-Last)
├── montecarlo.py                 # Monte-Carlo-basierte Lastprofil-Simulation
├── load_prediction_2week.py      # Modelle B1 & B2: Extrapolation & SLP-Kombi
├── evaluation.py                 # NMAE- und Preisabweichungsmetriken
├── customer_input_check.py       # Datenvorbereitung & Filterung
├── /data                         # Eingabedaten (Haushalte, PV, Preise, SLP)
├── /simulations_cache            # Zwischengespeicherte Simulationen (per Haushalt) um später schneller zu rechnen
├── secrets.json                  # API-Schlüssel (ausgeschlossen per `.gitignore`)
└── README.md                     # Projektdokumentation
```

## Weitere Entwicklungsmöglichkeiten: 
**Simulation**
- [ ] Randomisierung der 2-Wochen-Daten implementieren . Bisher nur auf zwei festen Wochen. Es kann aber Unterschiede geben, jenachdem wann gemessen wird.


**App**
- [ ] Amortationsdauer anpassbar (bspw. 5 und 10 Jahre) momentan nur 10 Jahre (mauell anpassbar über "years") siehe KOmmentare in savings.py
- [ ] Investitionsvolumen anpassbar (momentan nur 600€)
- [ ] Eingabe Nutzeranwendungsfreundlicher: konkrete Auswahlfelder (einfach nur Süd statt Asurichtungswinkel... )
- [ ] Eingabe Nutzeranwendungsfreundlicher: Standort nicht mit Koordinaten eingeben, sondern einfach mit PLZ oder genauer Adresse. Dafür wahrscheinlich API nötig
- [ ] 