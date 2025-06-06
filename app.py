import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Asumiendo que 'data' es tu JSON
data = {'total_count': 380,
 'results': [{'gid': 2018,
   'denominacion': 'CONSTITUCIÓN (DE HERMANOS MACHADO A TAVERNES BLANQUES)',
   'estado': 0,
   'idtramo': 282,
   'fiwareid': None,
   'geo_shape': {'type': 'Feature',
    'geometry': {'coordinates': [[-0.3703238195268041, 39.49847439201998],
      [-0.37010717326416565, 39.49960208697644],
      [-0.3700874152893759, 39.499694628098716],
      [-0.37006381690951845, 39.49978663184986],
      [-0.3700363934627394, 39.49987799947833],
      [-0.3700051719060921, 39.499968632495154],
      [-0.36997020243417633, 39.500058432937095],
      [-0.3699315000474089, 39.5001473110527],
      [-0.3698891262208219, 39.50023517814223],
      [-0.3698430959562572, 39.50032194445366],
      [-0.36979348268839846, 39.50040751254864],
      [-0.3697403362763767, 39.50049179346373],
      [-0.36968370658021643, 39.50057469823525]],
     'type': 'LineString'},
    'properties': {}},
   'geo_point_2d': {'lon': -0.3700778715218118, 'lat': 39.499551709139574}},
  {'gid': 2077,
   'denominacion': 'PUENTE DEL REAL HACIA VIVEROS',
   'estado': 0,
   'idtramo': 288,
   'fiwareid': None,
   'geo_shape': {'type': 'Feature',
    'geometry': {'coordinates': [[-0.36808641709687767, 39.476928883129574],
      [-0.369412562742749, 39.47566448461972]],
     'type': 'LineString'},
    'properties': {}},
   'geo_point_2d': {'lon': -0.3687494899198133, 'lat': 39.47629668387465}}]}

# Convertir el JSON a un DataFrame de Pandas
df = pd.DataFrame(data['results'])

# Función para determinar el color según el estado
def get_color(estado):
    if estado == 0:
        return 'green'
    elif estado == 1:
        return 'red'
    elif estado == 2:
        return 'blue'
    else:
        return 'gray'

# Crear un mapa centrado en la primera ubicación
m = folium.Map(location=[df['geo_point_2d'].iloc[0]['lat'], df['geo_point_2d'].iloc[0]['lon']], zoom_start=13)

# Iterar sobre cada calle y dibujar la línea en el mapa
for index, row in df.iterrows():
    coordinates = row['geo_shape']['geometry']['coordinates']
    estado = row['estado']
    color = get_color(estado)
    folium.PolyLine(locations=[(coord[1], coord[0]) for coord in coordinates], color=color, weight=5, opacity=0.7).add_to(m)

# Mostrar el mapa en Streamlit
st_folium(m)