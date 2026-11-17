# pages/details.py – Technische Detailanalysen
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np

dash.register_page(__name__, path="/details", name="Details")

layout = dbc.Container([
    html.H2(
        "Technische Details",
        className="fw-light border-bottom pb-2 mb-4"
    ),
    html.Div(id="details-content"),
], className="mt-4")


@callback(
    Output("details-content", "children"),
    Input("model-result-store", "data"),
)
def render_details(data):
    if not data:
        return dbc.Alert([
            html.Span("Noch keine Modelldaten vorhanden. "),
            dcc.Link("Dateneingabe", href="/", className="alert-link"),
        ], color="warning", className="shadow-sm")

    # ── Daten aus Store ──────────────────────────────────────────────────────
    hourly_load        = data.get("hourly_load_avg", [])
    hourly_load_pv     = data.get("hourly_load_avg_w_pv", [])
    solar_hourly       = data.get("solar_hourly_avg", [])
    monthly_load       = data.get("monthly_load_totals", [])
    solar_monthly      = data.get("solar_monthly_totals", [])
    heatmap_data       = data.get("monthly_hourly_heatmap", [])
    annual_consumption = data.get("annual_consumption", 0)
    solar_yield        = data.get("annual_solar_yield", 0)
    self_consumption   = data.get("self_consumption_sim_avg", 0)

    hours  = list(range(24))
    months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

    # ── 1. Tägliches Verbrauchsprofil ────────────────────────────────────────
    fig_hourly = go.Figure()

    if hourly_load:
        fig_hourly.add_trace(go.Scatter(
            x=hours, y=hourly_load,
            name="Verbrauch ohne PV",
            mode="lines+markers",
            line=dict(color="#636EFA", width=2),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(99,110,250,0.1)",
            hovertemplate="%{x}:00 Uhr – %{y:.3f} kWh<extra>Verbrauch</extra>"
        ))

    if hourly_load_pv:
        fig_hourly.add_trace(go.Scatter(
            x=hours, y=hourly_load_pv,
            name="Nettoverbrauch (mit PV)",
            mode="lines+markers",
            line=dict(color="#00CC96", width=2, dash="dash"),
            marker=dict(size=5),
            hovertemplate="%{x}:00 Uhr – %{y:.3f} kWh<extra>Nettoverbrauch</extra>"
        ))

    if solar_hourly:
        fig_hourly.add_trace(go.Scatter(
            x=hours, y=solar_hourly,
            name="PV-Erzeugung",
            mode="lines+markers",
            line=dict(color="#FFA15A", width=2),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(255,161,90,0.15)",
            hovertemplate="%{x}:00 Uhr – %{y:.3f} kWh<extra>PV-Ertrag</extra>"
        ))

    fig_hourly.update_layout(
        title={"text": "Ø Stündliches Lastprofil vs. PV-Erzeugung", "x": 0.5},
        xaxis=dict(
            title="Uhrzeit",
            tickmode="array",
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h}:00" for h in range(0, 24, 2)],
        ),
        yaxis=dict(title="Ø Leistung (kWh/h)", rangemode="tozero"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
        margin=dict(l=20, r=20, t=60, b=40),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        hovermode="x unified",
    )

    hourly_card = dbc.Card([
        dbc.CardHeader("Tägliches Verbrauchsprofil (Jahresdurchschnitt)", className="fw-bold"),
        dbc.CardBody([
            html.P(
                "Der Bereich zwischen Verbrauch und PV-Erzeugung, wo sich die Kurven überschneiden, "
                "entspricht dem direkten Eigenverbrauch – der Energie, die sofort selbst genutzt wird.",
                className="text-muted small mb-2"
            ),
            dcc.Graph(figure=fig_hourly, config={"displayModeBar": False}),
        ])
    ], className="mb-4 shadow rounded-3")

    # ── 2. Monat × Stunde Heatmap ─────────────────────────────────────────────
    heatmap_card_content = html.Div("Keine Heatmap-Daten vorhanden.", className="text-muted")
    if heatmap_data and len(heatmap_data) == 12:
        z_data  = heatmap_data  # 12 × 24 Matrix
        z_max   = max(max(row) for row in z_data)

        fig_heat = go.Figure(go.Heatmap(
            z=z_data,
            x=[f"{h}:00" for h in range(24)],
            y=months,
            colorscale="YlOrRd",
            zmin=0,
            zmax=z_max,
            colorbar=dict(title="kWh/h"),
            hovertemplate="Monat: %{y}<br>Uhrzeit: %{x}<br>Verbrauch: %{z:.3f} kWh<extra></extra>",
        ))
        fig_heat.update_layout(
            title={"text": "Verbrauch: Monat × Uhrzeit (Heatmap)", "x": 0.5},
            xaxis=dict(title="Uhrzeit", side="bottom"),
            yaxis=dict(title="Monat", autorange="reversed"),
            height=380,
            margin=dict(l=20, r=20, t=50, b=40),
            paper_bgcolor="#ffffff",
        )
        heatmap_card_content = dcc.Graph(figure=fig_heat, config={"displayModeBar": False})

    heatmap_card = dbc.Card([
        dbc.CardHeader("Verbrauchsmuster: Monat × Tageszeit", className="fw-bold"),
        dbc.CardBody([
            html.P(
                "Helle Felder zeigen Zeiten mit hohem Verbrauch. "
                "Erkennbar: winterliche Abendspitzen und sommerliche Mittagstäler durch PV-Kompensation.",
                className="text-muted small mb-2"
            ),
            heatmap_card_content,
        ])
    ], className="mb-4 shadow rounded-3")

    # ── 3. Monatliche Verbrauchs- & Solar-Balken ──────────────────────────────
    fig_monthly = go.Figure()
    if monthly_load:
        fig_monthly.add_trace(go.Bar(
            x=months[:len(monthly_load)],
            y=monthly_load,
            name="Verbrauch (kWh)",
            marker_color="#636EFA",
            hovertemplate="%{x}: %{y:.1f} kWh<extra>Verbrauch</extra>",
        ))
    if solar_monthly:
        fig_monthly.add_trace(go.Bar(
            x=months[:len(solar_monthly)],
            y=solar_monthly,
            name="PV-Ertrag (kWh)",
            marker_color="#FFA15A",
            hovertemplate="%{x}: %{y:.1f} kWh<extra>PV-Ertrag</extra>",
        ))

    # Selbstversorgungsgrad je Monat als Linie (Eigenverbrauchspotenzial)
    if monthly_load and solar_monthly:
        coverage = [
            min(s / l * 100, 100) if l > 0 else 0
            for s, l in zip(solar_monthly[:len(monthly_load)], monthly_load)
        ]
        fig_monthly.add_trace(go.Scatter(
            x=months[:len(coverage)],
            y=coverage,
            name="PV-Deckungsgrad (%)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#00CC96", width=2),
            marker=dict(size=6),
            hovertemplate="%{x}: %{y:.1f} %<extra>PV-Deckungsgrad</extra>",
        ))

    fig_monthly.update_layout(
        title={"text": "Monatlicher Verbrauch vs. PV-Ertrag", "x": 0.5},
        barmode="group",
        xaxis=dict(title="Monat"),
        yaxis=dict(title="Energie (kWh)", rangemode="tozero"),
        yaxis2=dict(
            title="PV-Deckungsgrad (%)",
            overlaying="y", side="right",
            rangemode="tozero", range=[0, 110],
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
        margin=dict(l=20, r=20, t=60, b=40),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        hovermode="x unified",
    )

    monthly_card = dbc.Card([
        dbc.CardHeader("Monatliche Energie-Übersicht", className="fw-bold"),
        dbc.CardBody([
            html.P(
                "Der PV-Deckungsgrad (grüne Linie) zeigt, wie viel Prozent des monatlichen Verbrauchs "
                "theoretisch durch die PV-Anlage gedeckt werden könnte.",
                className="text-muted small mb-2"
            ),
            dcc.Graph(figure=fig_monthly, config={"displayModeBar": False}),
        ])
    ], className="mb-4 shadow rounded-3")

    # ── 4. Energiefluss-Sankey ────────────────────────────────────────────────
    feed_in = max(solar_yield - self_consumption, 0)
    grid_draw = max(annual_consumption - self_consumption, 0)

    fig_sankey = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=["PV-Erzeugung", "Netz", "Eigenverbrauch", "Einspeisung", "Haushalt"],
            color=["#FFA15A", "#636EFA", "#00CC96", "#EF553B", "#AB63FA"],
            pad=20,
            thickness=20,
        ),
        link=dict(
            source=[0, 0, 1],
            target=[2, 3, 4],
            value=[
                round(self_consumption, 1),
                round(feed_in, 1),
                round(grid_draw, 1),
            ],
            color=["rgba(0,204,150,0.3)", "rgba(239,85,59,0.3)", "rgba(99,110,250,0.3)"],
            label=[
                f"Eigenverbrauch: {self_consumption:.0f} kWh",
                f"Einspeisung: {feed_in:.0f} kWh",
                f"Netzbezug: {grid_draw:.0f} kWh",
            ],
        )
    ))
    fig_sankey.update_layout(
        title={"text": "Jährlicher Energiefluss", "x": 0.5},
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="#ffffff",
        font=dict(size=13),
    )

    sankey_card = dbc.Card([
        dbc.CardHeader("Energiefluss-Diagramm (Jahresübersicht)", className="fw-bold"),
        dbc.CardBody([
            html.P(
                "Das Sankey-Diagramm zeigt, wie die erzeugte PV-Energie aufgeteilt wird: "
                "direkt selbst verbraucht vs. ins Netz eingespeist. Der Netzbezug deckt den restlichen Verbrauch.",
                className="text-muted small mb-2"
            ),
            dcc.Graph(figure=fig_sankey, config={"displayModeBar": False}),
        ])
    ], className="mb-4 shadow rounded-3")

    # ── 5. Kennzahlen-Zusammenfassung ─────────────────────────────────────────
    self_sufficiency = (self_consumption / annual_consumption * 100) if annual_consumption else 0
    self_consumption_rate = (self_consumption / solar_yield * 100) if solar_yield else 0

    stats_card = dbc.Card([
        dbc.CardHeader("Technische Kennzahlen", className="fw-bold"),
        dbc.CardBody(
            dbc.Row([
                dbc.Col(_stat_item("Jahresverbrauch",        f"{annual_consumption:.0f} kWh",    "bi bi-lightning-charge"), md=4),
                dbc.Col(_stat_item("PV-Jahresertrag",        f"{solar_yield:.0f} kWh",           "bi bi-sun"), md=4),
                dbc.Col(_stat_item("Eigenverbrauch",         f"{self_consumption:.0f} kWh",      "bi bi-house-check"), md=4),
                dbc.Col(_stat_item("Eigenverbrauchsanteil",  f"{self_consumption_rate:.1f} %",   "bi bi-percent"), md=4),
                dbc.Col(_stat_item("Autarkiegrad",           f"{self_sufficiency:.1f} %",        "bi bi-battery-charging"), md=4),
                dbc.Col(_stat_item("Einspeisung (ges.)",     f"{feed_in:.0f} kWh",               "bi bi-arrow-up-circle"), md=4),
            ])
        )
    ], className="mb-4 shadow-sm")

    return [
        stats_card,
        hourly_card,
        dbc.Row([
            dbc.Col(heatmap_card, md=7),
            dbc.Col(sankey_card, md=5),
        ]),
        monthly_card,
    ]


def _stat_item(label, value, icon_class):
    return html.Div([
        html.I(className=f"{icon_class} me-2 text-primary"),
        html.Span(label + ": ", className="text-muted small"),
        html.Span(value, className="fw-bold"),
    ], className="mb-2")
