# pages/home.py
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import datetime
import re

dash.register_page(__name__, path="/", name="Dateneingabe")
# bi bi-info-circle

# Define the PV card separately
pv_card = dbc.Card([
    dbc.CardHeader("Deine PV-Anlagendaten"),
    dbc.CardBody([

        dbc.Row([
            dbc.Label([
                html.I(className="bi bi-info-circle me-2 .text-white-50"),
                "Breitengrad"
            ], width=4, id="label-latitude"),
            dbc.Col(dbc.Input(id="latitude", type="number", placeholder="z. B. 50.0"), width=3),
        ], className="mb-3"),
        dbc.Tooltip("Geografische Breite in Dezimalgrad (z. B. 50.0 für Karlsruhe).", target="label-latitude", placement="bottom"),

        dbc.Row([
            dbc.Label([
                html.I(className="bi bi-info-circle me-2 .text-white-50"),
                "Längengrad"
            ], width=4, id="label-longitude"),
            dbc.Col(dbc.Input(id="longitude", type="number", placeholder="z. B. 8.0"), width=3),
        ], className="mb-3"),
        dbc.Tooltip("Geografische Länge in Dezimalgrad (z. B. 8.0 für Karlsruhe).", target="label-longitude", placement="bottom"),

        dbc.Row([
            dbc.Label([
                html.I(className="bi bi-info-circle me-2 .text-white-50"),
                "Kapazität (kWp)"
            ], width=4, id="label-capacity"),
            dbc.Col(dbc.Input(id="capacity", type="number", placeholder="z. B. 0.8"), width=3),
        ], className="mb-3"),
        dbc.Tooltip("Nennleistung der PV-Anlage in Kilowatt Peak. Für den Standardfall wird von 0.8 kW ausgegangen.", target="label-capacity", placement="bottom"),

        dbc.Row([
            dbc.Label([
                html.I(className="bi bi-info-circle me-2 .text-white-50"),
                "Systemverluste (%)"
            ], width=4, id="label-loss"),
            dbc.Col(dbc.Input(id="system-loss", type="number", placeholder="z. B. 10"), width=3),
        ], className="mb-3"),
        dbc.Tooltip("Verluste durch Kabel, Wechselrichter etc. in Prozent. Für den Standardfall wird von 10 % ausgegangen.", target="label-loss", placement="bottom"),

        dbc.Row([
            dbc.Label([
                html.I(className="bi bi-info-circle me-2 .text-white-50"),
                "Neigungswinkel (°)"
            ], width=4, id="label-tilt"),
            dbc.Col(dbc.Input(id="tilt", type="number", placeholder="z. B. 90"), width=3),
        ], className="mb-3"),
        dbc.Tooltip("Winkel zwischen Modulfläche und Horizontalebene. Für den Standardfall wird von 90° ausgegangen.", target="label-tilt", placement="bottom"),

        dbc.Row([
            dbc.Label([
                html.I(className="bi bi-info-circle me-2 .text-white-50"),
                "Azimuthwinkel (°)"
            ], width=4, id="label-azimuth"),
            dbc.Col(dbc.Input(id="azimuth", type="number", placeholder="z. B. 180"), width=3),
        ], className="mb-3"),
        dbc.Tooltip("Richtung der Modulfläche: 180° = Süden, 90° = Osten, 270° = Westen.", target="label-azimuth", placement="bottom"),

    ])

], className="mb-4", style={"backgroundColor": "#ffffff", "color": "primary", "borderRadius": "8px", "width": "35rem"})

layout = dbc.Container([
    html.H2(
        ["Persönliche Dateneingabe"],
        className=".text-black-50 fw-light border-bottom pb-2 mb-4"
    ),
    dbc.Form([
        # Jahresverbrauchsfeld
        dbc.Row([
            dbc.Label("Name", width=2, id="label-household-name"),
            dbc.Col(
                dbc.Input(id="householdname", type="text", placeholder="z. B. SFH3_P_TOT"),
                width=3
            )
        ], className="mb-3"),
        
        dbc.Row([
            #dbc.Label([html.I(className="bi bi-upload me-2 text-info"), "CSV-Datei hochladen"], width=2, id="label-upload"),
            dbc.Label(["CSV-Datei hochladen"], width=3, id="label-upload"),
            dbc.Col(
                dcc.Upload(
                    id="upload-data",
                    children=dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-file-earmark-arrow-up", style={"fontSize": "1.5rem"}),
                                html.Div("Datei hierher ziehen oder klicken", className="mt-2 text-muted")
                            ], className="text-center")
                        ]),
                        className="border border-secondary shadow-sm",
                        style={"backgroundColor": "#f5f5f5", "color": "primary", "borderRadius": "8px", "cursor": "pointer", "width": "35rem"}
                    ),
                    multiple=False
                ),
                width=10
            )
        ], className="mb-3"),
        dbc.Tooltip("Lade deine CSV-Datei mit Verbrauchsdaten hoch.", target="label-upload", placement="bottom"),
        html.Div(id="upload-output", className="mt-4"),
       
        # Jahresverbrauchsfeld
        dbc.Row([
            dbc.Label("Jahresverbrauch (kWh)", width=4, id="label-consumption"),
            dbc.Col(
                dbc.Input(id="annual-consumption", type="number", placeholder="z. B. 3200", min=0),
                width=3
            )
        ], className="mb-3"),
        dbc.Tooltip("Gesamter Stromverbrauch des letzten Jahres in kWh.", target="label-consumption", placement="bottom"),
        
        
        #Daten abfrage
        dbc.Row([
            dbc.Label("Startdatum Verbauchsdaten", width=4, id="label-start-date"),
            dbc.Col(
                dbc.Input(
                    id="start-date",
                    type="text",
                    placeholder="01.01.2019",
                    debounce=True  # Wert wird erst nach Verlassen des Feldes weitergegeben
                ),
                width=3
            )
        ], className="mb-3"),
        dbc.Tooltip("TT.MM.JJJJ", target="label-start-date", placement="bottom"),

        dbc.Row([
            dbc.Label("Enddatum Verbauchsdaten", width=4, id="label-end-date"),
            dbc.Col(
                dbc.Input(
                    id="end-date",
                    type="text",
                    placeholder="14.01.2019",
                    debounce=True  # Wert wird erst nach Verlassen des Feldes weitergegeben
                ),
                width=3
            )
        ], className="mb-3"),
        dbc.Tooltip("TT.MM.JJJJ", target="label-end-date", placement="bottom"),

        dbc.Row([
            dbc.Label("Startdatum Forecast", width=4, id="label-start-date-forecast"),
            dbc.Col(
                dbc.Input(
                    id="start-date-forecast",
                    type="text",
                    placeholder="01.01.2020",
                    debounce=True  # Wert wird erst nach Verlassen des Feldes weitergegeben
                ),
                width=3
            )
        ], className="mb-3"),
        dbc.Tooltip("TT.MM.JJJJ", target="label-start-date-forecast", placement="bottom"),
    

        pv_card,

        dbc.Row([
            dbc.Col([
                dbc.Button("Bestätigen", id="submit-button", color="success", outline=True, className="me-2"),
                dbc.Button("Zurücksetzen", id="reset-button", color="danger", outline=True)
            ])
        ], className="mt-3"),

    ]),
    html.Div([
        dcc.Link(dbc.Button("Zu den Ergebnissen", color="primary"), href="/savings")
    ])
])


# Beispielhafte Warnanzeige bei Fehler
# Funktion zum Prüfen des Formats TT.MM.JJJJ
def is_valid_date_format(date_str):
    return bool(re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str))

@callback(
    Output("start-date", "invalid"),
    Output("end-date", "invalid"),
    Output("start-date-forecast", "invalid"),
    Input("start-date", "value"),
    Input("end-date", "value"),
    Input("start-date-forecast", "value"),
)
def validate_dates(start_date, end_date, forecast_start):
    invalid_start = not is_valid_date_format(start_date) if start_date else False
    invalid_end = not is_valid_date_format(end_date) if end_date else False
    invalid_forecast = not is_valid_date_format(forecast_start) if forecast_start else False
    return invalid_start, invalid_end, invalid_forecast
