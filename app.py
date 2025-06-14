import streamlit as st
import polars as pl
import pydeck as pdk
import pandas as pd
import holidays
import datetime
import json
import joblib
import numpy as np

st.set_page_config(layout="wide", page_title="Estado Carreteras Valencia")
st.title("Estado carreteras Valencia")

today = datetime.date.today()
selected_date = st.date_input(
    "Selecciona una fecha:",
    value=today,
    key="date_selector"
)

now = datetime.datetime.now().time()
selected_time = st.time_input(
    "Selecciona una hora:",
    step=datetime.timedelta(minutes=15),
    key="time_selector"
)

selected_datetime = datetime.datetime.combine(selected_date, selected_time)

st.write(f"Has seleccionado: **{selected_datetime.strftime('%d/%m/%Y %H:%M')}**")

def get_business_day(fecha: datetime.datetime, pais: str = 'ES') -> bool:
    """
    Verifica si una fecha es un día laborable, considerando fines de semana y festivos.

    Args:
        fecha: El objeto datetime.datetime a verificar.
        pais: El código ISO 3166-1 alpha-2 del país (ej. 'ES' para España).
              Puedes pasar una lista de países si aplica a múltiples jurisdicciones.
    """
    if fecha.weekday() >= 5:  # 5 es sábado, 6 es domingo
        return False

    dias_festivos = holidays.country_holidays(pais, years=fecha.year)

    return fecha.date() not in dias_festivos


def predict_traffic_status(
    model_path: str,
    target_datetime: datetime.datetime,
    country_code: str = 'ES' # Código de país para los días festivos
    ) -> int:
    """
    Carga un modelo .joblib y predice el estado del tráfico para una fecha y hora dadas.

    Args:
        model_path (str): La ruta al archivo del modelo .joblib.
        target_datetime (datetime.datetime): La fecha y hora para la cual se realizará la predicción.
        country_code (str): El código ISO del país para determinar los días festivos
                            (por ejemplo, 'ES' para España).

    Returns:
        int: La predicción del modelo para el estado del tráfico.
    """
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        print(f"Error: El archivo del modelo no se encontró en '{model_path}'")
        return -1

    year = target_datetime.year
    month = target_datetime.month
    day = target_datetime.day
    weekday = target_datetime.weekday()
    is_business_day = get_business_day(target_datetime, country_code)
    hour = target_datetime.hour

    features = np.array([[year, month, day, weekday, int(is_business_day), hour]])

    prediction = model.predict(features)[0]
    print(prediction)

    return prediction

def get_color_for_road(gid: str, current_datetime: datetime.datetime):
    model_path = f"models/model_{gid}.joblib"
    traffic_code = predict_traffic_status(model_path, current_datetime)

    if traffic_code == 0 or traffic_code == 5:
        # 0 Fluido, 5 Paso inferior fluido - Verde claro para indicar buen flujo
        return [0, 255, 0, 200]  # Verde brillante

    elif traffic_code == 1 or traffic_code == 6:
        # 1 Denso, 6 Paso inferior denso - Amarillo para indicar lentitud
        return [255, 255, 0, 200]  # Amarillo

    elif traffic_code == 2 or traffic_code == 7:
        # 2 Congestionado, 7 Paso inferior congestionado - Naranja para indicar tráfico pesado
        return [255, 165, 0, 200] # Naranja

    elif traffic_code == 3 or traffic_code == 8:
        # 3 Cortado, 8 Paso inferior cortado - Rojo para indicar interrupción total
        return [255, 0, 0, 200]  # Rojo

    elif traffic_code == 4 or traffic_code == 9:
        # 4 Sin datos, 9 Sin datos (paso inferior) - Gris para indicar falta de información
        return [128, 128, 128, 200] # Gris

    else:
        print("Codigo no reconocido:", traffic_code)
        # Código no reconocido - Blanco o un color por defecto para errores
        return [255, 255, 255, 255]


try:
    df = pd.read_csv("data/base_dataframe.csv")
except FileNotFoundError:
    st.error("Error: El archivo 'data/base_dataframe.csv' no se encontró. "
             "Asegúrate de que el archivo existe y la ruta es correcta.")
    st.stop()

geo_data = {}
for idx, row in df.iterrows():
    gid = row["gid"]
    geo_shape = json.loads(row["geo_shape"])
    name = row["Denominació / Denominación"]
    geo_data[gid] = {"name": name, "path": geo_shape["coordinates"]}

center_lat = 39.466
center_lon = -0.357

initial_view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=13,
    pitch=0,
)

layers = []
for gid in geo_data:
    df_line = pd.DataFrame([geo_data[gid]])
    
    current_road_color = get_color_for_road(gid, selected_datetime)

    line_layer = pdk.Layer(
        "PathLayer",
        df_line,
        get_path="path",
        get_color=current_road_color,
        get_width=5,
        width_min_pixels=2,
        pickable=True,
    )
    layers.append(line_layer)

st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v11",
        initial_view_state=initial_view_state,
        layers=layers,
    ),
    use_container_width=True,
    height=775,
)