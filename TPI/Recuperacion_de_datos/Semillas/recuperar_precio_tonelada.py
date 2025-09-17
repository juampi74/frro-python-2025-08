import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import pandas as pd

precio_dolar = 1359

# --------------------------------------------------------------------

#funcion - obtengo: soja, maiz, trigo, sorgo, cebada y girasol
def obtener_precios_por_tonelada():
    fecha = datetime.now().date()

    url = "https://www.bcp.org.ar/informes.asp?id_inf=24"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    precios = []

    otros_cultivos = ['Maní Runner']

    # Obtiene los <p> del div.tab_content > p
    for p in soup.select("div.tab_content > p"):
        cultivo = p.get_text(strip=True).replace('Ã­', 'i').replace(' ', '').lower()
        # Entra a la tabla siguiente al <p>
        tabla = p.find_next_sibling("table")
        if not tabla:
            continue

        filas = tabla.find_all("tr")
        # La fila 1 es el encabezado, la fila 2 tiene precios en ARS, la fila 3 tiene precios en USD 
        if len(filas) >= 2:
            celdas_ars = [td.get_text(strip=True) for td in filas[1].find_all("strong")]
            celdas_usd = [td.get_text(strip=True) for td in filas[2].find_all("strong")]
            
            if celdas_ars[2] != 's/c':
                precio = int(celdas_ars[2])
            elif celdas_ars[1] != 's/c':
                precio = int(celdas_ars[1])
            elif celdas_usd[1] != 's/c':
                precio = int(celdas_usd[1]) * precio_dolar
            elif celdas_usd[2] != 's/c':
                precio = int(celdas_usd[2]) * precio_dolar
            else: precio = 0

            if precio == 0:
                otros_cultivos.append(cultivo)
            else:
                precios.append([fecha, cultivo, precio])

    url = "https://www.bccba.org.ar/todas-las-pizzarras/"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    cards = soup.find_all("div", class_="pizarra-card")
    for cultivo in otros_cultivos:
        for card in cards:
            titulo = card.find("p", class_="pizarra-titulo")
            if titulo and cultivo.upper() in titulo.text.upper():
                precios_cultivo = card.find_all("p", class_="pizarra-precio")
                if len(precios) >= 2:
                    precio = int(float(precios_cultivo[0].text.strip().replace('$', '').replace('.', '').replace(',','.')))
                break
        precios.append([fecha, cultivo, precio])

    return precios

def recuperar_precios(lista:list=[], fecha=datetime.now().date()):

    csv_path = "Recuperacion_de_datos/Semillas/Archivos generados/precios_por_tonelada.csv"

    if not os.path.exists(csv_path):
        # Crear un DataFrame vacío con las columnas deseadas
        df = pd.DataFrame(columns=['fecha', 'cultivo_nombre', 'precio_x_tonelada'])
        
        # Guardar el CSV sin índice
        df.to_csv(csv_path, index=False)

    with open(csv_path, newline='', encoding="utf-8") as datos_precios:
        data = csv.reader(datos_precios)
        encabezado = next(data, None)
        datos_hoy = [fila for fila in data 
                     if datetime.strptime(fila[0], '%Y-%m-%d').date() == fecha]

    if not datos_hoy and fecha != datetime.now().date():
        print("No se encontraron datos para esa fecha.")

    if not datos_hoy:
        datos_hoy = obtener_precios_por_tonelada()
        with open(csv_path, 'w', newline='', encoding="utf-8") as datos_precios:
            writer = csv.writer(datos_precios)
            writer.writerow(['fecha', 'cultivo_nombre', 'precio_x_tonelada'])
            for fila in datos_hoy:
                cultivo = fila[1]
                if cultivo.lower() == "maní runner":
                    fila[1] = "maní"
                elif cultivo.lower() == "maiz":
                    fila[1] = "maíz"
            writer.writerows(datos_hoy)

    if lista:
        lista_precios = []
        for s in lista:  
            for d in datos_hoy:
                if s.lower() == d[1].lower():
                    lista_precios.append([s, d[2]])
                    break
        return lista_precios


    return datos_hoy

precios = recuperar_precios()
#for cultivo in precios:
    #print(f"Hoy {cultivo[0]} el valor de la tonelada de {cultivo[1]} es {cultivo[2]}")
# recuperar_precios() ->
#[['2025-08-12', 'trigo', '266540'], 
# ['2025-08-12', 'cebada', '243460'], 
# ['2025-08-12', 'maiz', '229770'], 
# ['2025-08-12', 'girasol', '407960'], 
# ['2025-08-12', 'soja', '385000'], 
# ['2025-08-12', 'sorgo', '229770'], 
# ['2025-08-12', 'Mani', '785715.0']]


#precios_algunos = recuperar_precios(["soja","cebada","trigo"])
# recuperar_precios(["soja","cebada","trigo"]) ->
#[['soja', '385000'], 
# ['cebada', '243460'], 
# ['trigo', '266540']]

# Si le pasas una lista con determinadas semillas, te devuelve solo esas.
# En cambio, si le pasas vacio devuelve todas.
# Siempre que no haya valores para esa fecha, la funcion guarda 
# en el .csv los valores de todos los cultivos, 
# para que cuando se necesiten ya esten guardados