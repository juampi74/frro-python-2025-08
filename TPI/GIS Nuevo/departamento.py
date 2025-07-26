##Tener descargado y en la misma carpeta el: Poligono Departamento Shapefile de la pagina: https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/CapasSIG
##Las coordenadas que da el mapa interactivo copiarlas en la variable geojson
import json
import geopandas as gpd
from shapely.geometry import shape

geojson = """
{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-64.337324,-33.142681],[-64.336681,-33.142834],[-64.336981,-33.143355],[-64.337625,-33.14322],[-64.337324,-33.142681]]]}}
"""
geojson_dict = json.loads(geojson)

# Convertir a geometría de shapely
mi_poligono = shape(geojson_dict["geometry"])

# Crear un GeoDataFrame con esa geometría
poligono_gdf = gpd.GeoDataFrame(index=[0], geometry=[mi_poligono], crs="EPSG:4326")

# Leer los departamentos desde el shapefile del IGN
departamentos = gpd.read_file("departamentoPolygon.shp")

# Asegurarse que ambos estén en el mismo sistema de coordenadas (WGS84 - EPSG:4326)
departamentos = departamentos.to_crs(epsg=4326)

# Hacer la intersección: encontrar qué departamentos intersectan con tu polígono
interseccion = gpd.overlay(departamentos, poligono_gdf, how="intersection")

##print("----------------------------------")
##print(departamentos.columns)
##print(departamentos[["gid", "objeto", "fna", "gna", "nam", "in1"]].head(10))
# Mostrar resultados
if not interseccion.empty:
    for _, row in interseccion.iterrows():
        print(
            f"Provincia: {row['fna']}, Departamento: {row['nam']}"
        )  ##ver porque a veces no sale la provincia
else:
    print("El polígono no intersecta con ningún departamento.")
