# app.py
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, page_container, page_registry
import controller


app = dash.Dash(__name__,
                use_pages=True,suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP, "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" ])

app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="WattWise",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dcc.Link("Dateneingabe", href="/", className="nav-link")),
            dbc.NavItem(dcc.Link("Ersparnisse", href="/savings", className="nav-link")),
            dbc.NavItem(dcc.Link("Details", href="/details", className="nav-link")),
        ]
    ),
    html.Hr(),
    dcc.Store(id="model-result-store", storage_type="session"), # << hier speichern wir Ergebnis & Eingaben
    page_container
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)