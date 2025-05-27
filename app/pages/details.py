# pages/details.py
import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/details", name="Details")

layout = dbc.Container([
    html.H2("📊 Technische Details"),

    html.P("Hier werden alle Modellparameter, Plots und Zeitreihen angezeigt."),
    html.Div("Noch in Arbeit...", className="text-muted")
])
