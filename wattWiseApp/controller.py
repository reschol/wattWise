# controller.py – Zentrale Logik zur Datenverarbeitung & Modellsteuerung

from dash import Input, Output, State, callback, html, callback_context, no_update, dcc
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from model import load_csv_as_df, save_dataframe_to_csv, run_model_pipeline
import traceback
#from plots import plot_user_friendly_consumption_profile, plot_daily_patterns_comparison, plot_layperson_friendly_profile


# -----------------------
# Upload-Callback: CSV verarbeiten & anzeigen
# -----------------------

@callback(
    Output("upload-output", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("householdname", "value"),  
    prevent_initial_call=True
)

def handle_csv_upload(contents, filename, hh_name):
    """Verarbeitet die hochgeladene CSV-Datei, speichert sie ab und zeigt eine Vorschau an."""
    if contents is None:
        return dbc.Alert("Keine Datei hochgeladen.", color="warning")

    try:
        df = load_csv_as_df(contents)
        saved_path = save_dataframe_to_csv(df, filename)
        
        # Spaltennamen ggf. angleichen für Output
        if "date" in df.columns and "Time" not in df.columns:
            df.rename(columns={"date": "Time"}, inplace=True)

        if "Time" not in df.columns or hh_name not in df.columns:
            return dbc.Alert("Die Datei muss mindestens die Spalten 'Time' und den angegebenen Haushaltsnamen enthalten.", color="danger")

        df_preview = df[["Time", hh_name]].head()

        return dbc.Card(
            dbc.CardBody([
            html.Div([
                html.H5("Datei erfolgreich verarbeitet", className="text-success"),
                html.H6(f"Dateiname: {filename}", className="mb-1"),
                html.P(f"Gespeichert unter: {saved_path}", className="text-muted mb-3"),
            ]),
            html.H6("Vorschau der ersten 5 Zeilen:", className="mb-2"),
            dbc.Table.from_dataframe(
                df_preview,
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,  # sorgt für responsives Verhalten
                className="w-50" # volle Breite der Card
            ),
            ]),
            className="shadow-sm border-start border-4 border-success",
        )
    except Exception as e:
        return dbc.Alert(f"Fehler beim Einlesen: {str(e)}", color="danger")



# -----------------------
# Haupt-Callback: Modell starten bei Klick
# -----------------------

@callback(
    Output("model-result-store", "data"),
    Output("submit-button", "children"),
    Output("submit-button", "color"),
    Output("submit-button", "outline"),
    Input("submit-button", "n_clicks"),
    Input("reset-button", "n_clicks"),
    State("householdname", "value"),
    State("upload-data", "contents"),
    State("latitude", "value"),
    State("longitude", "value"),
    State("capacity", "value"),
    State("system-loss", "value"),
    State("tilt", "value"),
    State("azimuth", "value"),
    State("annual-consumption", "value"),
    State("start-date", "value"),
    State("end-date", "value"),
    State("start-date-forecast", "value"),
    prevent_initial_call=True
)
def handle_model_submit(submit_clicks, reset_clicks, hh_name, file_contents, lat, lon, cap, loss, tilt, azimuth,
                        annual_cons, start_date, end_date, forecast_start):
    """Startet das Modell bei Klick auf 'Modell starten' oder setzt alles zurück bei Klick auf 'Zurücksetzen'."""

    
    triggered_id = callback_context.triggered_id

    # Abbruch-Button gedrückt → Store leeren
    if triggered_id == "reset-button":
        return {}, "Modell starten", "success", True
    
    # Submit gedrückt → Modell starten
    if triggered_id == "submit-button":
        if not submit_clicks or submit_clicks < 1:
            raise dash.exceptions.PreventUpdate
        try:
            if file_contents is None:
                return {}, "Bitte lade zuerst eine CSV-Datei hoch.", "warning", False
            
            df = load_csv_as_df(file_contents)

            if "Time" not in df.columns:
                df.rename(columns={"date": "Time"}, inplace=True)

            # Nur die relevanten Spalten behalten: Time & Load
            if hh_name not in df.columns:
                return {}, f"Die Spalte '{hh_name}' ist nicht in der CSV-Datei enthalten. Die CSV Datei muss die Spalten Time und bspw. SFH3_P_TOT haben", "danger", False
            else:
                df = df.drop(columns=[col for col in df.columns if col != "Time" and col != hh_name])
                df.rename(columns={hh_name: "Load"}, inplace=True)

            result = run_model_pipeline(hh_name, df, lat, lon, cap, loss, tilt, azimuth,
                                        annual_cons, start_date, end_date,
                                        forecast_start, model_choice ="montecarlo")
            
            #Plots erstellen und speichern
            #plot_user_friendly_consumption_profile(df=df, column_name="Load", start_date='2019-01-01') #Datei wird gespeichert als column_name+"barplots.svg"
            #plot_daily_patterns_comparison(df=df, column_name="Load", start_date=plot_start_date_formatted) #Datei wird gespeichert als column_name+"linechart_raw_patterns.svg"
            #plot_layperson_friendly_profile(df=df, column_name="Load", start_date=plot_start_date_formatted) #Datei wird gespeichert als column_name+"linechart_intervals.svg"
            
            
            # Eingaben & Ergebnis gemeinsam speichern
            result_data = {}
            result_data = {
                "latitude": lat,
                "longitude": lon,
                "capacity": cap,
                "loss": loss,
                "tilt": tilt,
                "azimuth": azimuth,
                "annual_consumption": annual_cons,
                "start_date": start_date,
                "end_date": end_date,
                "forecast_start": forecast_start,
                "model": result["model"],
                "status": result["status"],

                "dynamic_costs_wo_pv": result["dynamic_costs_wo_pv_all_sim"],
                "static_costs_wo_pv": result["static_costs_wo_pv_all_sim"],
                "avg_dynamic_costs_wo_pv": result["avg_dynamic_costs_wo_pv"],
                "avg_static_costs_wo_pv": result["avg_static_costs_wo_pv"],

                "dynamic_costs_w_pv": result["dynamic_costs_w_pv_all_sim"],
                "static_costs_w_pv": result["static_costs_w_pv_all_sim"],
                "avg_dynamic_costs_w_pv": result["avg_dynamic_costs_w_pv"],
                "avg_static_costs_w_pv": result["avg_static_costs_w_pv"],
                "annual_solar_yield": result["annual solar_yield"],
                "self_consumption_sim_avg": result["self_consumption_sim_avg"],

                # Aggregierte Profil-Daten für Visualisierungen
                "hourly_load_avg": result["hourly_load_avg"],
                "hourly_load_avg_w_pv": result["hourly_load_avg_w_pv"],
                "monthly_load_totals": result["monthly_load_totals"],
                "monthly_hourly_heatmap": result["monthly_hourly_heatmap"],
                "solar_hourly_avg": result["solar_hourly_avg"],
                "solar_monthly_totals": result["solar_monthly_totals"],
            }
            return result_data, "Modell erfolgreich berechnet!", "success", False

        except Exception as e:
            tb_str = traceback.format_exc()  # gibt den Traceback als String zurück
            return {}, f"Fehler beim Ausführen des Modells:\n{str(e)}\n\nTraceback:\n{tb_str}", "danger", False

