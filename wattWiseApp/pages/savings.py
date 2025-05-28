import dash
from dash import html, Input, Output, State, callback, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

dash.register_page(__name__, path="/savings", name="Ersparnisse")

layout = dbc.Container([
    html.H2(
        ["Mögliche Ersparnisse"],
        className=".text-black-50 fw-light border-bottom pb-2 mb-4"
    ),

    html.Div(id="conditional-content"),
    html.Div(id="details-section")
], className="mt-4")

# Callback: Zeigt je nach Zustand des Stores entweder Hinweis oder Ersparnisse
@callback(
    Output("conditional-content", "children"),
    Input("model-result-store", "data") # << Store aus controller.py
)
def display_initial_section(data):
    if not data:
        return dbc.Alert([
            html.Span("Noch keine Ergebnisse vorhanden. "),
            dcc.Link("Fülle deine Daten hier aus", href="/", className="alert-link")
        ], color="warning", className="shadow-sm")
    
    return dbc.Alert(
        [
            html.H4("Ersparnisse möglich!", className="alert-heading"),
            html.P("Basierend auf deinen Eingaben kann mit einem dynamischen Tarif gespart werden!"),
            html.Hr(),
            html.P(
                dbc.Button(
                    "Mehr Details zur Berechnung",
                    id="alert-toggle-fade",
                    color="success",
                    outline=True,
                    className="me-1",
                    n_clicks=0,
                ),
                className="mb-0",
            )
        ],
        color="success", className="shadow-sm",
    )

# Callback: Zeigt Details nur, wenn Button geklickt
@callback(
    Output("details-section", "children"),
    Input("alert-toggle-fade", "n_clicks"),
    State("model-result-store", "data"),
    prevent_initial_call=True
)
def show_detailed_summary(n, data):
    if not data:
        return None


    # Wenn DAten vorhanden, dann werden diese ausgegeben:
    eigene_angaben_card = dbc.Card([
            dbc.CardHeader("Deine Eingaben"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.Strong("Lastprofil geladen:"), width=3),
                    dbc.Col("✅", width=8),
                ]),
                dbc.Row([
                    dbc.Col(html.Strong("Modell:"), width=3),
                    dbc.Col(data["model"], width=8),
                ]),
                dbc.Row([
                    dbc.Col(html.Strong("Standort:"), width=3),
                    dbc.Col(f"{data['latitude']}°, {data['longitude']}°", width=8),
                ]),
                dbc.Row([
                    dbc.Col(html.Strong("PV-Anlage:"), width=3),
                    dbc.Col(f"{data['capacity']} kWp, {data['loss']} % Verluste", width=8),
                ]),
                dbc.Row([
                    dbc.Col(html.Strong("Ausrichtung:"), width=3),
                    dbc.Col(f"Neigung {data['tilt']}°, Azimut {data['azimuth']}°", width=8),
                ]),
                dbc.Row([
                    dbc.Col(html.Strong("Jahresverbrauch:"), width=3),
                    dbc.Col(f"{data['annual_consumption']} kWh", width=8),
                ]),
                dbc.Row([
                    dbc.Col(html.Strong("Datenzeitraum:"), width=3),
                    dbc.Col(f"{data['start_date']} – {data['end_date']}", width=8),
                ]),
                dbc.Row([
                    dbc.Col(html.Strong("Forecast ab:"), width=3),
                    dbc.Col(data["forecast_start"], width=8),
                ]),
            ])
        ], className="mt-4 shadow-sm")


    # Datenwerte (Platzhalter, falls einzelne fehlen)
    static_cost = data.get('static_costs', None)
    dynamic_cost = data.get('dynamic_costs', data.get('costs', None))
    pv_cost = data.get('dynamic_costs_pv', None)
    
    # Plotly Balkendiagramm
    fig = go.Figure(data=[
        go.Bar(name="Statisch", x=["Tarifoptionen"], y=[static_cost], marker_color="#6c757d"),
        go.Bar(name="Dynamisch", x=["Tarifoptionen"], y=[dynamic_cost], marker_color="#0d6efd"),
        go.Bar(name="Dynamisch + PV", x=["Tarifoptionen"], y=[pv_cost], marker_color="#198754")
    ])
    fig.update_layout(
        title={"text":"Vergleich forecasted annual Costs (€)", "x":0.5},
        title_font=dict(size=16),
        barmode="group",
        height=270,
        bargap=0.35,
        margin=dict(l=20, r=20, t=40, b=40),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#f9f9f9",
        font=dict(size=12),
        xaxis=dict(showticklabels=False),
        yaxis=dict(title="Kosten (€)", zeroline=False, gridcolor="#eaeaea"),
        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
    )
    # Card mit Darstellung + Chart
    kosten_card = dbc.Card([
        dbc.CardHeader("Kosten & Ergebnis", className="fw-bold"),
        dbc.CardBody(
            dbc.Row([
                # Linke Spalte: Text
                dbc.Col([
                    html.P(f"Statischer Tarif: {static_cost} €"),
                    html.P(f"Dynamischer Tarif: {dynamic_cost} €"),
                    html.P(f"Dynamisch + PV: {pv_cost} €"),
                ], width=6, className="d-flex align-items-center",style={"minHeight": "250px"} ),

                # Rechte Spalte: Balkendiagramm
                dbc.Col([
                    dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "250px"})
                ], width=6 )
            ])
        )
    ], className="mt-4 shadow rounded-3 border border-light-subtle")
        

    return html.Div([
        eigene_angaben_card,
        kosten_card,
        html.Div(
            dbc.Button("Zurücksetzen", id="reset-button", color="danger", className="mt-3"),
            className="text-end"  # rechtsbündig
        )
    ])
    
