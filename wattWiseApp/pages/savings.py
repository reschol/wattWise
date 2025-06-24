# Dash-Importe und Komponenten
from dash import Input, Output, State, callback, html, callback_context, no_update, dcc
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import base64
import os

# Import eigener Visualisierungsfunktionen


# Registrierung der Seite innerhalb von Dash
dash.register_page(__name__, path="/savings", name="Ersparnisse")


# Seitenlayout definieren (Container mit Überschrift und dynamischem Inhalt)
layout = dbc.Container([
    html.H2(
        ["Mögliche Ersparnisse"],
        className=".text-black-50 fw-light border-bottom pb-2 mb-4"
    ),

    # Optional: Radio-Buttons für die Auswahl des Abschreibungszeitraums. WEnn aktiviert, dann in Callback einfügen und display_results übergeben
    # html.Div([
    #     html.Label("Abschreibungszeitraum wählen:", className="fw-bold mb-2"),
    #     dcc.RadioItems(
    #         id="amortisation-years",
    #         options=[
    #             {"label": "10 Jahre", "value": 10},
    #             {"label": "5 Jahre", "value": 5}
    #         ],
    #         value=10,
    #         labelStyle={"display": "inline-block", "marginRight": "20px"},
    #         inputStyle={"marginRight": "6px"}
    #     )
    # ], className="mt-2 mb-4 p-3 border rounded shadow-sm bg-light"),

    html.Div(id="conditional-content"),
], className="mt-4")

# Callback zur Anzeige der Ergebnisse (wird ausgelöst, sobald Daten im Store sind)
@callback(
    Output("conditional-content", "children"),
    Input("model-result-store", "data"),  # Store aus controller.py
    # Input("amortisation-years", "value"), wenn übergeben werden soll, dann hier aktivieren und in display_results übergeben
)
def display_results(data):
    # 1. Datenprüfung – muss ganz am Anfang stehen!
    if not data:
        return dbc.Alert([
            html.Span("Noch keine Ergebnisse vorhanden. "),
            dcc.Link("Fülle deine Daten hier aus", href="/", className="alert-link")
        ], color="warning", className="shadow-sm")
    
    # 2. Daten extrahieren
    static_cost_wo_pv = data.get('static_costs_wo_pv')
    dynamic_cost_wo_pv = data.get('dynamic_costs_wo_pv')
    avg_dynamic_cost_wo_pv = data.get('avg_dynamic_costs_wo_pv')
    avg_static_cost_wo_pv = data.get('avg_static_costs_wo_pv')
    dynamic_cost_w_pv = data.get('dynamic_costs_w_pv')
    static_cost_w_pv = data.get('static_costs_w_pv')
    avg_dynamic_cost_w_pv = data.get('avg_dynamic_costs_w_pv')
    avg_static_cost_w_pv = data.get('avg_static_costs_w_pv')
    solar_yield = data.get('annual_solar_yield')
    self_consumption_sim_avg = data.get('self_consumption_sim_avg')  # Eigenverbrauchsanteil
    investment_cost = 600                                       # ggf. später ampassbar machen
    years = 10                                                  # ggf. später ampassbar machen

    # 3. Dynamische Wirtschaftlichkeitsrechnung mit gewählter Laufzeit
    cost_wo_wattwise = avg_static_cost_wo_pv
    cost_w_wattwise = investment_cost / years + avg_dynamic_cost_w_pv
    savings_first_10y = cost_wo_wattwise - cost_w_wattwise
    savings_after_10y = cost_wo_wattwise - avg_dynamic_cost_w_pv
    


     # 4. Weiter mit Hinweisen, Cards, usw.
    # Erfolgsmeldung als Hinweis oben
    hinweis = None
    if savings_first_10y > 0:
        hinweis = dbc.Alert(
            [
                html.H4("Ersparnisse möglich!", className="alert-heading"),
                html.P("Basierend auf deinen Eingaben kann mit einem dynamischen Tarif gespart werden!"),
            ],
            color="success", className="shadow-sm"
        )
    

    # Karte zur Anzeige der Nutzereingaben
    eigene_angaben_card = dbc.Card([
        dbc.CardHeader("Kontrolle: Deine Eingaben"),
        dbc.CardBody([
            dbc.Row([dbc.Col(html.Strong("Lastprofil geladen:"), width=3), dbc.Col("✅", width=8)]),
            dbc.Row([dbc.Col(html.Strong("Modell:"), width=3), dbc.Col(data["model"], width=8)]),
            dbc.Row([dbc.Col(html.Strong("Standort:"), width=3), dbc.Col(f"{data['latitude']}°, {data['longitude']}°", width=8)]),
            dbc.Row([dbc.Col(html.Strong("PV-Anlage:"), width=3), dbc.Col(f"{data['capacity']} kWp, {data['loss']} % Verluste", width=8)]),
            dbc.Row([dbc.Col(html.Strong("Ausrichtung:"), width=3), dbc.Col(f"Neigung {data['tilt']}°, Azimut {data['azimuth']}°", width=8)]),
            dbc.Row([dbc.Col(html.Strong("Jahresverbrauch:"), width=3), dbc.Col(f"{data['annual_consumption']} kWh", width=8)]),
            dbc.Row([dbc.Col(html.Strong("Datenzeitraum erfasst mit WattWise:"), width=3), dbc.Col(f"{data['start_date']} – {data['end_date']}", width=8)]),
            dbc.Row([dbc.Col(html.Strong("Forecast ab:"), width=3), dbc.Col(data["forecast_start"], width=8)]),
        ])
    ], className="mt-4 shadow-sm")

    # Wenn vorhandener Verbrauchsplot vorhanden → als Bild einbinden
    pattern_path = data.get("pattern_plot_path")
    if pattern_path and os.path.exists(pattern_path):
        with open(pattern_path, "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode()
        pattern_plot_component = html.Img(
            src=f"data:image/png;base64,{encoded_image}",
            style={"maxWidth": "100%", "marginTop": "30px", "border": "1px solid #ccc"}
        )
    else:
        pattern_plot_component = dbc.Alert("Verbrauchsprofil-Grafik konnte nicht geladen werden.", color="secondary")
    

    # Karte zur Anzeige der Kostenergebnisse & des Diagramms
    # Boxplot für die drei Kostenvariablen
    fig = go.Figure()
    fig.add_trace(go.Box(
        y=static_cost_wo_pv,
        name="Statisch (ohne PV)",
        boxmean='sd',
        marker_color='blue'
    ))
    fig.add_trace(go.Box(
        y=dynamic_cost_wo_pv,
        name="Dynamisch (ohne PV)",
        boxmean='sd',
        marker_color='orange'
    ))
    fig.add_trace(go.Box(
        y=dynamic_cost_w_pv,
        name="Dynamisch (mit PV)",
        boxmean='sd',
        marker_color='green'
    ))
    fig.update_layout(
        title={"text": "Kostenvergleich (Boxplot)", "x": 0.5},
        title_font=dict(size=16),
        height=270,
        margin=dict(l=20, r=20, t=40, b=40),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#f9f9f9",
        font=dict(size=12),
        yaxis=dict(title="Kosten (€)", zeroline=False, gridcolor="#eaeaea"),
        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
    )


    kostenverteilung_card = dbc.Card([
        dbc.CardHeader("Kostenverteilung (Boxplot)", className="fw-bold"),
        dbc.CardBody(
            dbc.Row([
                dbc.Col([
                    html.P("Die Boxplots zeigen die Verteilung der Monte-Carlo-Simulation der jährlichen Stromkosten je Tarifoption."),
                    html.Ul([
                        html.Li("Statisch: fester Preis, keine PV"),
                        html.Li("Dynamisch: stündliche Preise, ohne/mit PV"),
                        html.Li("Box = 25.–75. Perzentil, Linie = Median, Punkt = Ausreißer"),
                    ]),
                html.Small("Tipp: Ein Doppelklick auf das Diagramm setzt den Zoom zurück.", className="text-muted fst-italic")
                ], width=5, style={"minHeight": "250px"}),

                dbc.Col([
                    dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "250px"})
                ], width=7)
            ])
        )
    ], className="mt-4 shadow rounded-3 border border-light-subtle")
        
    

    # Amortisationskarte mit den Ergebnissen
    amortisations_card = dbc.Card([
        dbc.CardHeader("Wirtschaftlichkeitsrechnung", className="fw-bold"),
        
        dbc.CardBody([
            html.P(f"Ihr approximierter Jahresverbrauch beläuft sich auf {data['annual_consumption']} kWh pro Jahr."),
            html.Br(),
            html.P("Bei dieser Lösung mit"),
            html.Ul([
                html.Li(f"{int(data['capacity'] * 1000)} Watt Peakleistung"),
                html.Li("Ausrichtung: " + f"{data['tilt']}° Neigung, {data['azimuth']}° Azimut"),
            ]),
            html.Br(),
            html.P("Würden sich ergeben"),
            html.Ul([
                html.Li(f"{solar_yield} kWh PV Erzeugung"),
                html.Li(f"{round(self_consumption_sim_avg, 2)} kWh Eigenverbrauch"),
                #html.Li(f"{data.get('pv_feed_in', '—')} kWh Netzeinspeisung"), #TODO
                html.Li(f"{(self_consumption_sim_avg / solar_yield * 100):.2f}% Eigenverbrauchsanteil")
            ]),
            html.Br(),
            html.P("Amortisationsannahmen:"),
            html.Ul([
                html.Li(f"Abschreibung über {years} Jahre"),
                html.Li(f"Durchschnittlicher Preis für die gewählte Anlage: {investment_cost} €"),
            ]),
            html.Br(),
            html.P([
                "Kosten pro Jahr mit Lösung: ",
                html.Strong(f"{cost_w_wattwise:.2f} €")
            ]),
            html.P([
                "Kosten pro Jahr ohne Lösung: ",
                html.Strong(f"{cost_wo_wattwise:.2f} €")
            ]),
        ])
    ], className="mt-4 shadow-sm")

    sparen_hinweis = dbc.Alert([
        html.H4("Langfristige Einsparung", className="alert-heading"),
        html.P([
            "Mit der gewählten Option und den oben getroffenen Annahmen sparen Sie in den ersten 10 Jahren ",
            html.Strong(f"{savings_first_10y:.2f} Euro pro Jahr")
        ]),
        html.P([
            "Ab dem 11. Jahr sparen Sie ",
            html.Strong(f"{abs(savings_after_10y):.2f} Euro pro Jahr")
        ])
    ],
    color="success",
    className="mt-3 shadow-sm")
    
    
    
    # Reset-Button zum Leeren der gespeicherten Daten
    reset_button = html.Div(
        dbc.Button("Zurücksetzen", id="reset-button", color="danger", className="mt-3"),
        className="text-end"
    )

    # Rückgabe der gesamten Inhaltselemente als Liste
    return [hinweis, eigene_angaben_card, kostenverteilung_card, pattern_plot_component, amortisations_card, sparen_hinweis, reset_button]




# Reset-Funktion: Leert die gespeicherten Modell-Daten
@callback(
    Output("model-result-store", "data", allow_duplicate=True),
    Input("reset-button", "n_clicks"),
    prevent_initial_call=True
)
def reset_model_data(n_clicks):
    return None

