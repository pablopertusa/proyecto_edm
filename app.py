import streamlit as st
import pydeck as pdk
import pandas as pd
import datetime
import json

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

# Función para determinar el color de la carretera
# NOTA: Esta es una implementación de ejemplo para mostrar la reactividad.
# DEBES REEMPLAZAR LA LÓGICA DE ESTA FUNCIÓN CON LA TUYA PROPIA.
def get_color_for_road(gid: str, current_datetime: datetime.datetime):
    # Lógica de ejemplo: el color cambia con la hora del día
    hour = current_datetime.hour

    # Simulación de tráfico:
    # Mañana (6-9h) y tarde (17-20h): Rojo (congestión)
    # Mediodía (12-14h): Naranja (moderado)
    # Noche/Madrugada (fuera de esos rangos): Verde (fluido)

    if 6 <= hour < 9 or 17 <= hour < 20:
        return [255, 0, 0, 200]  # Rojo
    elif 12 <= hour < 14:
        return [255, 140, 0, 200]  # Naranja
    else:
        return [0, 200, 0, 200]  # Verde

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
    zoom=14,
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
    use_container_width=True, # Hace que el mapa ocupe todo el ancho disponible
    height=775, # Define una altura fija de 600 píxeles
)