import streamlit as st
import polars as pl
import pydeck as pdk
import pandas as pd
import holidays
import datetime
import json
import joblib
import numpy as np

st.set_page_config(
    layout="wide",
    page_title="Estado Carreteras Valencia",
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Montserrat', sans-serif;
    }

    .stApp {
        background-color: #1a1a2e; /* Fondo oscuro principal */
        color: #e0e0e0; /* Color de texto claro */
    }

    .st-emotion-cache-1hwfblv {
        background-color: #1a1a2e; /* Asegura que el contenedor principal también sea oscuro */
    }

    .st-emotion-cache-10qik0r {
        background-color: #2e2e4f; /* Fondo para contenedores/tarjetas */
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); /* Sombra más pronunciada para contraste */
        padding: 20px;
        margin-bottom: 20px;
    }

    h1 {
        color: #e94560; /* Color de título llamativo */
        text-align: center;
        font-size: 3em;
        margin-bottom: 30px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    h2 {
        color: #0f3460; /* Un azul oscuro para subtítulos */
        font-size: 2em;
        margin-bottom: 15px;
    }

    h3 {
        color: #e0e0e0; /* Asegura que los h3 sean claros */
    }

    .stDateInput, .stTimeInput {
        background-color: #2e2e4f; /* Fondo de inputs oscuro */
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stDateInput label, .stTimeInput label {
        color: #e0e0e0 !important; /* Color de label claro */
    }

    .stDateInput input, .stTimeInput input {
        color: #e0e0e0 !important; /* Color de texto de input claro */
        background-color: #1a1a2e !important;
        border: 1px solid #0f3460 !important;
    }

    .stButton>button {
        background-color: #e94560; /* Color de botón llamativo */
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 1.1em;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    .stButton>button:hover {
        background-color: #b82c42; /* Color de botón en hover */
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }

    .stTextInput>div>div>input {
        border-radius: 8px;
        padding: 10px;
    }

    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }

    .st-emotion-cache-eczf16 {
        padding-top: 0rem;
    }

    .stMarkdown p {
        color: #e0e0e0; /* Asegura que el texto Markdown sea claro */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Estado Carreteras Valencia")

with st.container():
    st.markdown("---")
    st.subheader("Selecciona la Fecha y Hora para la Predicción")
    col1, col2 = st.columns(2)

    with col1:
        today = datetime.date.today()
        selected_date = st.date_input(
            "Selecciona una fecha:",
            value=today,
            key="date_selector",
            help="Elige la fecha para la que quieres predecir el estado del tráfico."
        )

    with col2:
        now = datetime.datetime.now().time()
        selected_time = st.time_input(
            "Selecciona una hora:",
            step=datetime.timedelta(minutes=15),
            key="time_selector",
            help="Elige la hora (en intervalos de 15 minutos) para la predicción."
        )

    selected_datetime = datetime.datetime.combine(selected_date, selected_time)

    st.markdown(f"### Has seleccionado: <span style='color:#e94560; font-weight:bold;'>{selected_datetime.strftime('%d/%m/%Y %H:%M')}</span>", unsafe_allow_html=True)
    st.markdown("---")

def get_business_day(fecha: datetime.datetime, pais: str = 'ES') -> bool:
    if fecha.weekday() >= 5:
        return False

    dias_festivos = holidays.country_holidays(pais, years=fecha.year)

    return fecha.date() not in dias_festivos


def predict_traffic_status(
    model_path: str,
    target_datetime: datetime.datetime,
    country_code: str = 'ES'
    ) -> int:
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
        return [0, 200, 83, 200]
    elif traffic_code == 1 or traffic_code == 6:
        return [255, 230, 0, 200]
    elif traffic_code == 2 or traffic_code == 7:
        return [255, 140, 0, 200]
    elif traffic_code == 3 or traffic_code == 8:
        return [220, 20, 60, 200]
    elif traffic_code == 4 or traffic_code == 9:
        return [150, 150, 150, 200]
    else:
        print("Codigo no reconocido:", traffic_code)
        return [255, 255, 255, 255]

try:
    df = pd.read_csv("data/base_dataframe.csv")
except FileNotFoundError:
    st.error("Error: El archivo 'data/base_dataframe.csv' no se encontró. Asegúrate de que el archivo existe y la ruta es correcta.")
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

st.subheader("Mapa del Estado del Tráfico en Valencia")
st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v11", # Cambio a estilo de mapa oscuro
        initial_view_state=initial_view_state,
        layers=layers,
        tooltip={"text": "{name}"}
    ),
    use_container_width=True,
    height=600,
)

st.markdown(
    """
    <div style='text-align: center; margin-top: 30px;'>
        <p style='font-size: 0.9em; color: #e0e0e0;'>
            Esta aplicación predice el estado del tráfico en las carreteras de Valencia
            basándose en la fecha y hora seleccionadas.
            <br>
            Los colores en el mapa indican:
            <br>
            <span style='color: rgb(0, 200, 83);'>&#9632; Verde: Fluido</span> |
            <span style='color: rgb(255, 230, 0);'>&#9632; Amarillo: Denso</span> |
            <span style='color: rgb(255, 140, 0);'>&#9632; Naranja: Congestionado</span> |
            <span style='color: rgb(220, 20, 60);'>&#9632; Rojo: Cortado</span> |
            <span style='color: rgb(150, 150, 150);'>&#9632; Gris: Sin datos</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
