from dash import Input, Output, State, callback, html
import dash_bootstrap_components as dbc
from model import load_csv_as_df, save_dataframe_to_csv, run_model_pipeline


@callback(
    Output("upload-output", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True
)

def handle_csv_upload(contents, filename):
    if contents is None:
        return dbc.Alert("Keine Datei hochgeladen.", color="warning")

    try:
        df = load_csv_as_df(contents)
        saved_path = save_dataframe_to_csv(df, filename)
        return dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H5("Datei erfolgreich verarbeitet", className="text-success"),
                    html.H6(f"Dateiname: {filename}", className="mb-1"),
                    html.P(f"Gespeichert unter: {saved_path}", className="text-muted mb-3"),
                ]),
                html.H6("Vorschau der ersten 5 Zeilen:", className="mb-2"),
                dbc.Table.from_dataframe(df.head(), striped=True, bordered=True, hover=True),
            ]),
            className="shadow-sm border-start border-4 border-success"
        )
    except Exception as e:
        return dbc.Alert(f"Fehler beim Einlesen: {str(e)}", color="danger")


#Modell Input
# Callback: Modellstart bei Buttonklick
@callback(
    Output("model-result-store", "data"), # << speichern Ergebnis im Store
    Output("submit-button", "children"), # << leitet auf Seite "/savings" um
    Output("redirect", "pathname"),
    Input("submit-button", "n_clicks"),
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
    State("model-choice", "value"),
    prevent_initial_call=True
)
def handle_model_submit(n_clicks, lat, lon, cap, loss, tilt, azimuth,
                        annual_cons, start_date, end_date, forecast_start, model_choice):

    try:
        result = run_model_pipeline(lat, lon, cap, loss, tilt, azimuth,
                                    annual_cons, start_date, end_date,
                                    forecast_start, model_choice)
        
        # Eingaben & Ergebnis gemeinsam speichern
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
            "costs": result["costs"],
        }
        return result_data, dbc.Alert("Modell erfolgreich ausgeführt!", color="success"), "/savings"


    except Exception as e:
        return dbc.Alert(f"Fehler beim Ausführen des Modells: {str(e)}", color="danger")

