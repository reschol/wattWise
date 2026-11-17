# WattWise – Personalisierte Analyse von Balkon-PV und dynamischen Stromtarifen

WattWise ist ein Software-Prototyp, der auf Basis von **nur zwei Wochen gemessener Verbrauchsdaten** eines Haushalts abschätzt, ob sich ein **dynamischer Stromtarif** und/oder eine **Balkon-PV-Anlage** lohnen. Statt eines Standardlastprofils, wie es gängige Online-Rechner verwenden, wird das individuelle Verbrauchsmuster des Haushalts auf ein ganzes Jahr hochgerechnet und mit realen Spotmarktpreisen und simulierten PV-Erträgen kombiniert.

Das Repository enthält
- eine **Dash-Web-App**, in die Nutzer*innen ihr 2-Wochen-Lastprofil hochladen und Kosten, Ersparnisse und Amortisation einer Balkon-PV-Anlage interaktiv auswerten können, und
- den **Analyse-Code**, mit dem verschiedene Prognosemodelle an 21 realen Haushalten verglichen wurden.

## Hintergrund & Mitwirkende

WattWise ist ein ENZo Real-World Project am KIT (2024–2026) von Oliver Resch und Philipp Fritz.

Die Prognosemodelle, die Kostenberechnung und die erste Version der Web-App wurden von **Hannah Heimpel** im Rahmen einer Spezialveranstaltung Wirtschaftsinformatik (2024/2025) entwickelt, betreut von Oliver Resch. Anschließend wurde die App vom Projektteam erweitert (2026: zusätzliche Visualisierungen, Detailseite, Vorbereitung der Veröffentlichung).

Die Hilfsfunktionen für den Datenabruf von ENTSO-E und Renewables.ninja (`src/utils/`) basieren auf dem Projekt *Agri-PV Plant Optimization* von Joshua Spreng.

## Installation

Getestet mit Python 3.11.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

### API-Schlüssel

Benötigt werden zwei (kostenlose) API-Zugänge:
- [Renewables.ninja](https://www.renewables.ninja/) – API-Token für PV-Erzeugungsdaten
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) – API-Key für Spotmarktpreise

Lege im Hauptverzeichnis eine Datei `secrets.json` an:

```json
{
    "ninja_token": "DEIN_RENEWABLES_NINJA_TOKEN",
    "entsoe_api_key": "DEIN_ENTSOE_API_KEY"
}
```

Die Datei ist per `.gitignore` ausgeschlossen und darf **niemals committet** werden.

## Nutzung der Web-App

```bash
cd wattWiseApp
python app.py
```

Die App läuft anschließend unter http://127.0.0.1:8050/ und besteht aus drei Seiten:

| Seite | Inhalt |
|---|---|
| **Dateneingabe** | Upload des 2-Wochen-Lastprofils, Jahresverbrauch, Standort und PV-Konfiguration (Leistung, Neigung, Ausrichtung, Verluste) |
| **Ersparnisse** | Kennzahlen, Kostenvergleich fixer vs. dynamischer Tarif mit und ohne PV, Verteilung der Monte-Carlo-Ergebnisse, Amortisationsverlauf |
| **Details** | Tagesprofil, Heatmap Monat × Stunde, Energiefluss (Sankey), monatlicher Verbrauch und PV-Deckungsgrad |

### Format der CSV-Datei

Die hochgeladene Datei muss stündliche Verbrauchswerte enthalten:

| Spalte | Inhalt | Beispiel |
|---|---|---|
| `Time` (alternativ `date`) | Zeitstempel (stündlich) | `2019-01-01 00:00` |
| `<Name>` | Verbrauch je Stunde in kWh | `0.24` |

Die Verbrauchsspalte kann beliebig heißen (z. B. `SFH3_P_TOT` oder `Haushalt_1`). Ihr Name wird im Eingabeformular angegeben.

```csv
Time,SFH3_P_TOT
2019-01-01 00:00,0.24
2019-01-01 01:00,0.20
2019-01-01 02:00,0.22
...
```

Beispieldateien liegen unter `data/` (z. B. `load_profile_2019_2weeks_01012019_14012019.csv`, enthält mehrere Haushalte als Spalten, etwa `SFH3_P_TOT`).

**Hinweis:** Spotmarktpreise liegen für 2019, 2020 und 2024 vor. Das Prognosejahr muss daher eines dieser Jahre sein, sofern keine weiteren Preise über `src/utils/entsoe_client.py` heruntergeladen werden.

## Methodik

### Prognosemodelle

Aus den zwei Wochen Messdaten wird ein stündliches Lastprofil für ein ganzes Jahr erzeugt:

| Modell | Beschreibung |
|---|---|
| **A – Monte Carlo** | 100 zufällig erzeugte Jahreslastprofile auf Basis der Tagesprofile aus den zwei Wochen; saisonale Faktoren aus dem Standardlastprofil (SLP) 2019. Liefert eine Verteilung möglicher Verläufe inkl. Unsicherheit. **Wird in der App verwendet.** |
| **B1 – 2-Wochen-Profil** | Das mittlere Tagesprofil (werktags und Wochenende) wird auf das gesamte Jahr übertragen. |
| **B2 – Hybridmodell** | Kombination aus B1 und SLP, gewichtet nach Saison: in der Saison des Messzeitraums überwiegt das gemessene Profil, außerhalb dominiert das SLP. |

### PV-Integration

Die PV-Erzeugung wird stündlich über Renewables.ninja simuliert. Die Netzbezugslast ergibt sich als

```
Netzbezug = max(Verbrauch − PV-Erzeugung, 0)
```

### Kostenberechnung

- **Fixer Tarif:** durchschnittlicher Haushaltsstrompreis des Prognosejahres (BDEW)
- **Dynamischer Tarif:** stündlicher Day-Ahead-Spotpreis (ENTSO-E, DE-LU) zuzüglich eines verbrauchsabhängigen Aufschlags für Netzentgelte, Abgaben und Steuern (19,71 ct/kWh) und einer Grundgebühr (15,73 €/Monat, angelehnt an Tibber 2024)
- jeweils mit und ohne Balkon-PV

### Ergebnisse der Modellevaluation

Bewertet an 21 Einfamilienhaushalten des WPuQ-Datensatzes mit je 14 Tagen Messdaten (Normalized Mean Absolute Error der stündlichen Last):

| Modell | Ø NMAE | Std.-Abw. |
|---|---|---|
| A – Monte Carlo | 61,1 % | 10,2 % |
| B1 – 2-Wochen-Profil | 50,9 % | 9,0 % |
| B2 – Hybridmodell | 48,9 % | 9,9 % |

Die Jahreskosten mit dynamischem Tarif ohne PV werden von allen Modellen sehr genau getroffen (Ø Abweichung < 1 €). Mit PV unterschätzen B1 und B2 die Kosten deutlich (−13 € bzw. −19 €), während das Monte-Carlo-Modell am genauesten ist (+4,5 €). 30 statt 14 Tage Messdaten verbessern die Ergebnisse nur minimal.

## Projektstruktur

```text
.
├── wattWiseApp/                  # Dash-Web-App
│   ├── app.py                    #   Einstiegspunkt, Layout und Navigation
│   ├── controller.py             #   Callbacks: Upload, Validierung, Modellstart
│   ├── model.py                  #   Modell-Pipeline: Simulation, PV, Preise, Kosten
│   ├── plots.py                  #   ältere Matplotlib-Plots (derzeit nicht verwendet)
│   └── pages/                    #   Seiten: home.py, savings.py, details.py
├── main.py                       # Skript zur Modellevaluation über alle Haushalte
├── montecarlo.py                 # Modell A: Monte-Carlo-Simulation, SLP, Kostenfunktionen
├── load_prediction_2week_slp.py  # Modelle B1 und B2
├── pv_prediction.py              # PV-Daten (API/CSV) und Netzbezugsberechnung
├── evaluation.py                 # NMAE- und Kostenabweichungsmetriken
├── customer_input_check.py       # Datenaufbereitung und Filterung
├── src/utils/                    # API-Clients für ENTSO-E und Renewables.ninja
├── data/                         # Eingabedaten (Lastprofile, PV, Preise, SLP)
├── local_input_data/             # Haushaltsdatensatz (WPuQ, stündlich)
├── simulations_cache/            # zwischengespeicherte Monte-Carlo-Simulationen
├── output_load/                  # Prognoseergebnisse
├── archive/                      # Jupyter-Notebooks aus der Entwicklungsphase
├── all_runs_results_14days.json  # Evaluationsergebnisse (30 Läufe à 21 Haushalte)
└── requirements.txt
```

## Mögliche Weiterentwicklungen

**Modell**
- Messzeitraum randomisieren: bisher werden feste zwei Wochen verwendet, die Ergebnisse können aber je nach Jahreszeit der Messung variieren.
- Batteriespeicher in die Simulation aufnehmen.

**App**
- Investitionskosten (derzeit 600 €) und Abschreibungsdauer (derzeit 10 Jahre) im Formular anpassbar machen (siehe `savings.py`).
- Eingabe vereinfachen: Auswahlfelder (z. B. „Süd“ statt Azimutwinkel) und Standortangabe per PLZ oder Adresse statt Koordinaten.

## Datenquellen & Lizenzen

Dieses Repository enthält (aufbereitete) Daten Dritter. Bitte die jeweiligen Lizenzen beachten:

| Daten | Quelle | Lizenz |
|---|---|---|
| Haushaltslastprofile (`local_input_data/` sowie daraus abgeleitete Daten in `data/*.csv`, `simulations_cache/`, `output_load/`) | WPuQ-Datensatz: Schlemminger, M., Ohrdes, T., Schneider, E., Knoop, M. (2022): *Dataset on electrical single-family house and heat pump load profiles in Germany*. Scientific Data 9, 56. https://doi.org/10.1038/s41597-022-01156-1 – für dieses Projekt auf Stundenwerte aggregiert und um Zeitmerkmale ergänzt | CC BY 4.0 |
| Day-Ahead-Spotpreise DE-LU (`data/entsoe_data/`) | ENTSO-E Transparency Platform, https://transparency.entsoe.eu/ | CC BY 4.0 |
| PV-Erzeugungszeitreihen (`data/renewables_ninja_data/`) | Renewables.ninja, https://www.renewables.ninja/ (Pfenninger & Staffell 2016; Staffell & Pfenninger 2016) | CC BY-NC 4.0 |
| Standardlastprofil H0 2019 (`data/slp/`) | vom Netzbetreiber veröffentlichtes Standardlastprofil | gemäß Veröffentlichung des Netzbetreibers |
| Jährliche Haushaltsstrompreise (`data/electricity_prices_yearly/`) | BDEW-Strompreisanalyse | – |

## Lizenz

Der Quellcode steht unter der MIT-Lizenz, siehe [LICENSE](LICENSE). Die Lizenz gilt nicht für die oben aufgeführten Daten Dritter.
