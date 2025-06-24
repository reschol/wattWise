# pages/home.py
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
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
            dbc.Col(dbc.Input(id="latitude", type="number", placeholder="z. B. 50.0", valid=False, invalid=False), width=3),
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
                "Systemverluste (decimal)"
            ], width=4, id="label-loss"),
            dbc.Col(dbc.Input(id="system-loss", type="number", placeholder="z. B. 0.1"), width=3),
        ], className="mb-3"),
        dbc.Tooltip("Verluste durch Kabel, Wechselrichter etc. in Prozent. Für den Standardfall wird von 0.1 (10%) ausgegangen.", target="label-loss", placement="bottom"),

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
        # Haushaltsname
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
                dcc.Loading(
                    id="loading-model",
                    type="circle",
                    children=[
                        dbc.Button("Modell starten", id="submit-button", color="success", outline=True)
                    ]
                )
            ], width="auto"),
            dbc.Col([
                dcc.Link(dbc.Button("Zu den Ergebnissen", color="primary"), href="/savings")
            ], width="auto"),
            dbc.Col([
                dbc.Button("Zurücksetzen", id="reset-button", color="danger", outline=True)
            ], width="auto"),
            

        ], className="mt-4 g-2"), # g-2: Abstand zw. Spalten

        
    ]),
])


# Beispielhafte Warnanzeige bei Fehler
# Funktion zum Prüfen des Formats TT.MM.JJJJ
def is_valid_date_format(date_str):
    return bool(re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str))

@callback(
    Output("start-date", "invalid"), Output("start-date", "valid"),
    Output("end-date", "invalid"), Output("end-date", "valid"),
    Output("start-date-forecast", "invalid"), Output("start-date-forecast", "valid"),
    Output("annual-consumption", "invalid"), Output("annual-consumption", "valid"),
    Output("latitude", "invalid"), Output("latitude", "valid"),
    Output("longitude", "invalid"), Output("longitude", "valid"),
    Output("capacity", "invalid"), Output("capacity", "valid"),
    Output("system-loss", "invalid"), Output("system-loss", "valid"),
    Output("tilt", "invalid"), Output("tilt", "valid"),
    Output("azimuth", "invalid"), Output("azimuth", "valid"),

    Input("start-date", "value"),
    Input("end-date", "value"),
    Input("start-date-forecast", "value"),
    Input("annual-consumption", "value"),
    Input("latitude", "value"),
    Input("longitude", "value"),
    Input("capacity", "value"),
    Input("system-loss", "value"),
    Input("tilt", "value"),
    Input("azimuth", "value"),
)
def validate_inputs(start_date, end_date, forecast_start,
                    consumption, lat, lon, cap, loss, tilt, azimuth):
    
    # Datum: TT.MM.JJJJ
    invalid_start = start_date is not None and not is_valid_date_format(start_date)
    valid_start = start_date is not None and is_valid_date_format(start_date)

    invalid_end = end_date is not None and not is_valid_date_format(end_date)
    valid_end = end_date is not None and is_valid_date_format(end_date)

    invalid_forecast = forecast_start is not None and not is_valid_date_format(forecast_start)
    valid_forecast = forecast_start is not None and is_valid_date_format(forecast_start)

    # Jahresverbrauch: realistisch 0–20.000 kWh
    invalid_consumption = consumption is not None and (consumption <= 0 or consumption > 20000)
    valid_consumption = consumption is not None and (0 < consumption <= 20000)

    # Breitengrad: realistisch 30–55 (für DE)
    invalid_lat = lat is not None and not (30 <= lat <= 55)
    valid_lat = lat is not None and (30 <= lat <= 55)

    # Längengrad: realistisch 5–15 (für DE)
    invalid_lon = lon is not None and not (5 <= lon <= 15)
    valid_lon = lon is not None and (5 <= lon <= 15)

    # Kapazität: realistisch 0.1–20 kWp
    invalid_cap = cap is not None and not (0.1 <= cap <= 20)
    valid_cap = cap is not None and (0.1 <= cap <= 20)

    # Systemverluste: nur zwischen 0 und 1
    invalid_loss = loss is not None and not (0 <= loss <= 1)
    valid_loss = loss is not None and (0 <= loss <= 1)

    # Neigungswinkel: 0–90°
    invalid_tilt = tilt is not None and not (0 <= tilt <= 90)
    valid_tilt = tilt is not None and (0 <= tilt <= 90)

    # Azimuthwinkel: 0–360°
    invalid_azimuth = azimuth is not None and not (0 <= azimuth <= 360)
    valid_azimuth = azimuth is not None and (0 <= azimuth <= 360)

    return (
        invalid_start, valid_start,
        invalid_end, valid_end,
        invalid_forecast, valid_forecast,
        invalid_consumption, valid_consumption,
        invalid_lat, valid_lat,
        invalid_lon, valid_lon,
        invalid_cap, valid_cap,
        invalid_loss, valid_loss,
        invalid_tilt, valid_tilt,
        invalid_azimuth, valid_azimuth
    )
