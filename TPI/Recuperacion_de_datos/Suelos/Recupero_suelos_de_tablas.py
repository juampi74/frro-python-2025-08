import pandas as pd

def recupero_datos_suelo():
    # Cargar los CSV
    sites = pd.read_csv('Bases_de_datos/Suelo/SISLAC_site.csv')
    layers = pd.read_csv('Bases_de_datos/Suelo/SISLAC_layers.csv')

    # Elegir solo algunas columnas
    sites_collums = sites[['profile_identifier', 'latitude', 'longitude', 'country_code']]
    layers_collums = layers[['profile_identifier', 'bulk_density', 'ca_co3', 'coarse_fragments', 'ecec', 'conductivity', 
                            'organic_carbon', 'ph', 'clay', 'silt', 'sand', 'water_retention']]

    # Filtro datos innesesarios
    sites_collums = sites_collums[sites_collums['country_code'] == 'ARG']

    # Hacer un join (merge) usando site_id
    merged = pd.merge(sites_collums, layers_collums, on='profile_identifier', how='inner')

    merged_collums = merged[['latitude', 'longitude', 'bulk_density', 'ca_co3', 'coarse_fragments', 
                            'ecec', 'conductivity', 'organic_carbon', 'ph', 'clay', 'silt', 'sand', 'water_retention']]

    print(merged_collums.head())

    merged_collums.to_csv('Recuperacion_de_datos/Suelos/suelo_unido.csv', index=False)

recupero_datos_suelo()