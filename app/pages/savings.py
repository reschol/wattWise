# pages/savings.py
import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/savings", name="Ersparnisse")

layout = dbc.Container([
    html.H2("💰 Mögliche Ersparnisse"),

    dbc.Alert("Basierend auf deinen Eingaben können bis zu 23 % eingespart werden!", color="success"),

    html.Ul([
        html.Li("Optimierter Stromverbrauch durch Modellierung"),
        html.Li("Eigenverbrauch der PV-Anlage erhöht"),
        html.Li("CO₂-Ausstoß um 14 % reduziert"),
    ])
])
