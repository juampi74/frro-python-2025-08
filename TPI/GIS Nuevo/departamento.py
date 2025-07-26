##Tener descargado y en la misma carpeta el: Poligono Departamento Shapefile de la pagina: https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/CapasSIG
##1- entrar a https://geojson.io/
##2- dibujar el poligono
##3- Descargar el geojson y ponerlo en la misma carpeta que este .py
import geopandas as gpd

# Leer el polígono desde tu archivo geojson
poligono = gpd.read_file("map.geojson")

# Leer los departamentos desde el shapefile del IGN
departamentos = gpd.read_file("departamentoPolygon.shp")

# Asegurarse que ambos estén en el mismo sistema de coordenadas (WGS84 - EPSG:4326)
poligono = poligono.to_crs(epsg=4326)
departamentos = departamentos.to_crs(epsg=4326)

# Hacer la intersección: encontrar qué departamentos intersectan con tu polígono
interseccion = gpd.overlay(departamentos, poligono, how="intersection")

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
