# Dash-Importe und Komponenten
from dash import Input, Output, State, callback, html, callback_context, no_update, dcc
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np

# Registrierung der Seite innerhalb von Dash
dash.register_page(__name__, path="/savings", name="Ersparnisse")


# Seitenlayout definieren (Container mit Überschrift und dynamischem Inhalt)
layout = dbc.Container([
    html.H2(
        "Mögliche Ersparnisse",
        className="fw-light border-bottom pb-2 mb-4"
    ),
    html.Div(id="conditional-content"),
], className="mt-4")


def make_kpi_card(title, value, subtitle, color, icon_class):
    """Erstellt eine kompakte KPI-Karte."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon_class} fs-3 text-{color} mb-1"),
                html.H5(title, className="text-muted mb-1", style={"fontSize": "0.85rem"}),
                html.H3(value, className=f"text-{color} fw-bold mb-0"),
                html.Small(subtitle, className="text-muted"),
            ], className="text-center")
        ])
    ], className=f"shadow-sm border-top border-4 border-{color} h-100")


# Callback zur Anzeige der Ergebnisse (wird ausgelöst, sobald Daten im Store sind)
@callback(
    Output("conditional-content", "children"),
    Input("model-result-store", "data"),
)
def display_results(data):
    # 1. Datenprüfung
    if not data:
        return dbc.Alert([
            html.Span("Noch keine Ergebnisse vorhanden. "),
            dcc.Link("Fülle deine Daten hier aus", href="/", className="alert-link")
        ], color="warning", className="shadow-sm")

    # 2. Daten extrahieren
    static_cost_wo_pv      = data.get('static_costs_wo_pv')
    dynamic_cost_wo_pv     = data.get('dynamic_costs_wo_pv')
    dynamic_cost_w_pv      = data.get('dynamic_costs_w_pv')
    static_cost_w_pv       = data.get('static_costs_w_pv')
    avg_dynamic_cost_wo_pv = data.get('avg_dynamic_costs_wo_pv')
    avg_static_cost_wo_pv  = data.get('avg_static_costs_wo_pv')
    avg_dynamic_cost_w_pv  = data.get('avg_dynamic_costs_w_pv')
    avg_static_cost_w_pv   = data.get('avg_static_costs_w_pv')
    solar_yield            = data.get('annual_solar_yield')
    self_consumption       = data.get('self_consumption_sim_avg')
    investment_cost        = 600
    years                  = 10

    # 3. Wirtschaftlichkeitsrechnung
    baseline = avg_static_cost_wo_pv
    costs_dynamic_w_pv_total = investment_cost / years + avg_dynamic_cost_w_pv
    costs_static_w_pv_total  = investment_cost / years + avg_static_cost_w_pv

    savings_first_10y = baseline - costs_dynamic_w_pv_total
    savings_after_10y = baseline - avg_dynamic_cost_w_pv

    self_consumption_rate = (self_consumption / solar_yield * 100) if solar_yield else 0

    # Amortisationszeit berechnen
    annual_net_savings = baseline - avg_dynamic_cost_w_pv
    if annual_net_savings > 0:
        breakeven_years = investment_cost / annual_net_savings
        breakeven_str = f"≈ {breakeven_years:.1f} Jahre"
    else:
        breakeven_str = "Nicht rentabel"

    # ── 4. KPI-Karten ─────────────────────────────────────────────────────────
    kpi_row = dbc.Row([
        dbc.Col(make_kpi_card(
            "Jährl. Einsparung (10 J.)",
            f"{savings_first_10y:+.0f} €",
            "vs. statisch ohne PV",
            "success" if savings_first_10y > 0 else "danger",
            "bi bi-piggy-bank"
        ), xs=12, sm=6, lg=3, className="mb-3"),
        dbc.Col(make_kpi_card(
            "Langfristige Einsparung",
            f"{savings_after_10y:+.0f} €/Jahr",
            "ab Jahr 11 (ohne Abschreibung)",
            "primary",
            "bi bi-graph-up-arrow"
        ), xs=12, sm=6, lg=3, className="mb-3"),
        dbc.Col(make_kpi_card(
            "Amortisationszeit",
            breakeven_str,
            "Investitionsrückfluss",
            "warning",
            "bi bi-clock-history"
        ), xs=12, sm=6, lg=3, className="mb-3"),
        dbc.Col(make_kpi_card(
            "PV Eigenverbrauch",
            f"{self_consumption_rate:.1f} %",
            f"{self_consumption:.0f} kWh / {solar_yield:.0f} kWh",
            "info",
            "bi bi-sun"
        ), xs=12, sm=6, lg=3, className="mb-3"),
    ], className="mb-2")

    # ── 5. Amortisationsverlauf-Diagramm ──────────────────────────────────────
    years_x = list(range(0, 16))
    cum_static_wo  = [baseline * y for y in years_x]
    cum_dynamic_wo = [avg_dynamic_cost_wo_pv * y for y in years_x]
    cum_static_w   = [investment_cost + avg_static_cost_w_pv * y for y in years_x]
    cum_dynamic_w  = [investment_cost + avg_dynamic_cost_w_pv * y for y in years_x]

    fig_amort = go.Figure()
    fig_amort.add_trace(go.Scatter(
        x=years_x, y=cum_static_wo,
        name="Statisch (ohne PV) — Basis",
        line=dict(color="#636EFA", width=2, dash="dot"),
        hovertemplate="%{y:.0f} €<extra>Statisch ohne PV</extra>"
    ))
    fig_amort.add_trace(go.Scatter(
        x=years_x, y=cum_dynamic_wo,
        name="Dynamisch (ohne PV)",
        line=dict(color="#EF553B", width=2, dash="dash"),
        hovertemplate="%{y:.0f} €<extra>Dynamisch ohne PV</extra>"
    ))
    fig_amort.add_trace(go.Scatter(
        x=years_x, y=cum_static_w,
        name="Statisch + PV",
        line=dict(color="#AB63FA", width=2),
        hovertemplate="%{y:.0f} €<extra>Statisch + PV</extra>"
    ))
    fig_amort.add_trace(go.Scatter(
        x=years_x, y=cum_dynamic_w,
        name="Dynamisch + PV (WattWise)",
        line=dict(color="#00CC96", width=3),
        fill="tonexty",
        fillcolor="rgba(0,204,150,0.08)",
        hovertemplate="%{y:.0f} €<extra>Dynamisch + PV</extra>"
    ))

    # Break-even-Linie
    if annual_net_savings > 0:
        be = investment_cost / annual_net_savings
        fig_amort.add_vline(
            x=be, line_dash="dash", line_color="gray",
            annotation_text=f"Break-even: {be:.1f} J.",
            annotation_position="top right"
        )

    fig_amort.update_layout(
        title={"text": "Kumulierte Stromkosten über 15 Jahre", "x": 0.5},
        xaxis=dict(title="Jahr", tickmode="linear", dtick=2),
        yaxis=dict(title="Kumulierte Kosten (€)", tickformat=",.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
        margin=dict(l=20, r=20, t=60, b=40),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        hovermode="x unified",
    )

    amort_card = dbc.Card([
        dbc.CardHeader("Kumulierte Kostenentwicklung über Zeit", className="fw-bold"),
        dbc.CardBody([
            html.P(
                "Das Diagramm zeigt, wie sich die Gesamtstromkosten je Szenario über 15 Jahre aufaddieren. "
                "Die grüne Fläche zeigt den Vorteil der WattWise-Lösung (dynamischer Tarif + PV). "
                "Die gestrichelte Linie markiert den Break-even-Punkt, ab dem sich die PV-Investition amortisiert.",
                className="text-muted small mb-2"
            ),
            dcc.Graph(figure=fig_amort, config={"displayModeBar": False}),
        ])
    ], className="mb-4 shadow rounded-3")

    # ── 6. Jahreskosten-Vergleichsdiagramm ────────────────────────────────────
    scenarios = [
        "Statisch (ohne PV)",
        "Dynamisch (ohne PV)",
        "Statisch + PV*",
        "Dynamisch + PV* (WattWise)",
    ]
    avg_costs = [baseline, avg_dynamic_cost_wo_pv, avg_static_cost_w_pv, avg_dynamic_cost_w_pv]
    bar_colors = ["#636EFA", "#EF553B", "#AB63FA", "#00CC96"]
    savings_vs_base = [0, baseline - avg_dynamic_cost_wo_pv,
                       baseline - avg_static_cost_w_pv, baseline - avg_dynamic_cost_w_pv]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=avg_costs,
        y=scenarios,
        orientation="h",
        marker_color=bar_colors,
        text=[f"{c:.0f} €  (–{s:.0f} €)" if s > 0 else f"{c:.0f} €"
              for c, s in zip(avg_costs, savings_vs_base)],
        textposition="outside",
        hovertemplate="%{x:.2f} €<extra>%{y}</extra>",
    ))
    fig_bar.update_layout(
        title={"text": "Ø Jahreskosten je Szenario", "x": 0.5},
        xaxis=dict(title="Ø Jahreskosten (€)", tickformat=",.0f"),
        yaxis=dict(autorange="reversed"),
        height=280,
        margin=dict(l=10, r=120, t=40, b=40),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        showlegend=False,
    )

    bar_card = dbc.Card([
        dbc.CardHeader("Jährliche Durchschnittskosten im Vergleich", className="fw-bold"),
        dbc.CardBody([
            html.P("*inkl. Abschreibung der PV-Investition über 10 Jahre nicht enthalten — "
                   "reiner Betriebsverbrauch.",
                   className="text-muted small mb-2"),
            dcc.Graph(figure=fig_bar, config={"displayModeBar": False}),
        ])
    ], className="mb-4 shadow rounded-3")

    # ── 7. Kostenverteilung Boxplot ────────────────────────────────────────────
    fig_box = go.Figure()
    box_traces = [
        (static_cost_wo_pv,  "Statisch (ohne PV)",  "#636EFA"),
        (dynamic_cost_wo_pv, "Dynamisch (ohne PV)", "#EF553B"),
        (static_cost_w_pv,   "Statisch (mit PV)",   "#AB63FA"),
        (dynamic_cost_w_pv,  "Dynamisch (mit PV)",  "#00CC96"),
    ]
    for y_data, name, color in box_traces:
        fig_box.add_trace(go.Box(
            y=y_data, name=name, boxmean="sd",
            marker_color=color,
            hovertemplate="%{y:.2f} €<extra>" + name + "</extra>"
        ))
    fig_box.update_layout(
        title={"text": "Monte-Carlo Kostenverteilung (100 Simulationen)", "x": 0.5},
        height=300,
        margin=dict(l=20, r=20, t=50, b=40),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        yaxis=dict(title="Jahreskosten (€)", gridcolor="#eaeaea"),
        showlegend=False,
    )

    boxplot_card = dbc.Card([
        dbc.CardHeader("Kostenverteilung über 100 Monte-Carlo-Simulationen", className="fw-bold"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.P("Die Boxplots zeigen die Bandbreite der simulierten Jahreskosten. "
                           "Schmale Boxen bedeuten geringe Unsicherheit."),
                    html.Ul([
                        html.Li("Box = 25.–75. Perzentil (typischer Bereich)"),
                        html.Li("Linie = Median"),
                        html.Li("Punkt = Mittelwert (σ-Linie = Standardabweichung)"),
                    ], className="small text-muted"),
                ], width=4),
                dbc.Col(
                    dcc.Graph(figure=fig_box, config={"displayModeBar": False}),
                    width=8
                ),
            ])
        ])
    ], className="mb-4 shadow rounded-3")

    # ── 8. Eingaben-Karte ──────────────────────────────────────────────────────
    eigene_angaben_card = dbc.Card([
        dbc.CardHeader("Kontrolle: Deine Eingaben"),
        dbc.CardBody([
            dbc.Row([dbc.Col(html.Strong("Modell:"),          width=4), dbc.Col(data["model"],                                              width=8)]),
            dbc.Row([dbc.Col(html.Strong("Standort:"),        width=4), dbc.Col(f"{data['latitude']}°N, {data['longitude']}°O",            width=8)]),
            dbc.Row([dbc.Col(html.Strong("PV-Anlage:"),       width=4), dbc.Col(f"{data['capacity']} kWp, {data['loss']*100:.0f} % Verluste", width=8)]),
            dbc.Row([dbc.Col(html.Strong("Ausrichtung:"),     width=4), dbc.Col(f"Neigung {data['tilt']}°, Azimut {data['azimuth']}°",     width=8)]),
            dbc.Row([dbc.Col(html.Strong("Jahresverbrauch:"), width=4), dbc.Col(f"{data['annual_consumption']} kWh",                       width=8)]),
            dbc.Row([dbc.Col(html.Strong("Datenzeitraum:"),   width=4), dbc.Col(f"{data['start_date']} – {data['end_date']}",              width=8)]),
            dbc.Row([dbc.Col(html.Strong("Forecast ab:"),     width=4), dbc.Col(data["forecast_start"],                                    width=8)]),
        ])
    ], className="mb-4 shadow-sm")

    # ── 9. Wirtschaftlichkeitstabelle ──────────────────────────────────────────
    amortisations_card = dbc.Card([
        dbc.CardHeader("Wirtschaftlichkeitsrechnung", className="fw-bold"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.P(f"PV-Ertrag: {solar_yield:.0f} kWh/Jahr"),
                    html.P(f"Eigenverbrauch: {self_consumption:.0f} kWh/Jahr ({self_consumption_rate:.1f} %)"),
                    html.P(f"Investition: {investment_cost} € (abgeschrieben über {years} J.)"),
                ], width=5),
                dbc.Col([
                    dbc.Table([
                        html.Thead(html.Tr([
                            html.Th("Szenario"),
                            html.Th(f"Ø Kosten erste {years} J. (€/J.)", style={"textAlign": "center"}),
                            html.Th("Ø Kosten ab J. 11 (€/J.)", style={"textAlign": "center"}),
                        ])),
                        html.Tbody([
                            html.Tr([
                                html.Td("Statisch, ohne PV"),
                                html.Td(f"{baseline:.2f} €", colSpan=2, style={"textAlign": "center", "fontWeight": "500"}),
                            ]),
                            html.Tr([
                                html.Td("Dynamisch, ohne PV"),
                                html.Td(f"{avg_dynamic_cost_wo_pv:.2f} €", colSpan=2, style={"textAlign": "center"}),
                            ]),
                            html.Tr([
                                html.Td("Statisch + PV"),
                                html.Td(f"{costs_static_w_pv_total:.2f} €", style={"textAlign": "center"}),
                                html.Td(f"{avg_static_cost_w_pv:.2f} €", style={"textAlign": "center"}),
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Dynamisch + PV (WattWise)")),
                                html.Td(html.Strong(f"{costs_dynamic_w_pv_total:.2f} €"), style={"textAlign": "center", "color": "#00CC96"}),
                                html.Td(html.Strong(f"{avg_dynamic_cost_w_pv:.2f} €"), style={"textAlign": "center", "color": "#00CC96"}),
                            ]),
                        ])
                    ], bordered=True, hover=True, responsive=True, striped=True, size="sm", className="mb-0")
                ], width=7),
            ])
        ])
    ], className="mb-4 shadow-sm")

    # ── 10. Ergebnis-Hinweis ───────────────────────────────────────────────────
    if savings_first_10y > 0:
        sparen_alert = dbc.Alert([
            html.H5("Mit der WattWise-Lösung sparen Sie:", className="alert-heading"),
            dbc.Row([
                dbc.Col(html.Div([html.Strong(f"{savings_first_10y:.2f} €/Jahr"), html.Div("in den ersten 10 Jahren", className="small")]), className="text-center"),
                dbc.Col(html.Div([html.Strong(f"{savings_after_10y:.2f} €/Jahr"), html.Div("ab Jahr 11 (Anlage abbezahlt)", className="small")]), className="text-center"),
                dbc.Col(html.Div([html.Strong(breakeven_str), html.Div("bis zur Amortisation", className="small")]), className="text-center"),
            ])
        ], color="success", className="mb-4 shadow-sm")
    else:
        sparen_alert = dbc.Alert(
            f"Mit den gegebenen Annahmen ist die Investition in den ersten {years} Jahren noch nicht rentabel "
            f"({savings_first_10y:.2f} €/Jahr). Langfristig (ab Jahr 11) spart die Lösung {savings_after_10y:.2f} €/Jahr.",
            color="warning", className="mb-4 shadow-sm"
        )

    reset_button = html.Div(
        dbc.Button("Zurücksetzen", id="reset-button", color="danger", outline=True, className="mt-2"),
        className="text-end mb-4"
    )

    return [
        sparen_alert,
        kpi_row,
        amort_card,
        dbc.Row([
            dbc.Col(bar_card, md=6),
            dbc.Col(boxplot_card, md=6),
        ], className="mb-2"),
        amortisations_card,
        eigene_angaben_card,
        reset_button,
    ]


# Reset-Funktion
@callback(
    Output("model-result-store", "data", allow_duplicate=True),
    Input("reset-button", "n_clicks"),
    prevent_initial_call=True
)
def reset_model_data(n_clicks):
    # Der Button wird dynamisch eingefügt; Dash löst den Callback dabei ohne Klick aus.
    # Nur bei echtem Klick zurücksetzen, sonst gingen die Ergebnisse beim Öffnen der Seite verloren.
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    return None
