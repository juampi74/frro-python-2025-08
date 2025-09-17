import random
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import squarify
# Utiliza openpyxl tambien
import numpy as np

import pickle
with open("model/cultivo_a_entero.pkl", "rb") as f:
    cultivo_a_entero = pickle.load(f)

from Red_neuronal.My_GBM import main as utilizar_GBM, limpiar_df
from Pred_Clima.pred_cond_climaticas import main as predecir_datos_clima  

# GENERAL
'''
La idea es crear poblaciones con los mismos datos de suelo dependiendo del departamento y un clima predecido de aca a 14 meses,
diferenciandose en la semilla utilizada y el área a cultivar por semilla.
'''

SEMILLAS = ['girasol', 'soja', 'maíz', 'trigo', 'sorgo', 'cebada', 'maní']

def pred_toneladas(totalha, depto, lon, lat):
    individuo = [totalha] * len(SEMILLAS) 
    toneladas = red_neuronal(individuo, depto, lon, lat)
    return toneladas

def obtener_precios():
    # Recupero precios de la tonelada de semilla
    from Recuperacion_de_datos.Semillas.recuperar_precio_tonelada import recuperar_precios
    #df_precios = pd.read_csv("Recuperacion_de_datos/Semillas/Archivos generados/precios_por_tonelada.csv")
    lista_precios = recuperar_precios()
    #df_precios = df_precios.tail(7)
    lista_precios_hoy = [fila[1:] for fila in lista_precios]
    precios_dict = dict(lista_precios_hoy)
    return precios_dict


def completoCromosoma(maximo, cantidad_genes=7):
    cromosoma = [random.random() for _ in range(cantidad_genes)]
    suma = sum(cromosoma)
    cromosoma = [(gen / suma) * maximo for gen in cromosoma]
    return cromosoma
       

def generarPoblacion(cantidadCromosomas, cantidadGenes, maximo):          
    poblacion = [] * cantidadCromosomas
    for _ in range(cantidadCromosomas):
        cromosoma = completoCromosoma(maximo, cantidadGenes)
        poblacion.append(cromosoma)
    return poblacion

#Funcion Objetivo original

def funcionObjetivo(x, precio):
    # Pasa por la red neuronal
    obj = x * precio  
    return obj
    
## calcular FO MODIF (TARDA MENOS)
def calculadorFuncionObjetivo(poblacion, toneladas, area): 
    objetivos = []

    # Recupero precios de la tonelada de semilla
    from Recuperacion_de_datos.Semillas.recuperar_precio_tonelada import recuperar_precios
    #df_precios = pd.read_csv("Recuperacion_de_datos/Semillas/Archivos generados/precios_por_tonelada.csv")
    lista_precios = recuperar_precios()
    #df_precios = df_precios.tail(7)
    lista_precios_hoy = [fila[1:] for fila in lista_precios]
    precios_dict = dict(lista_precios_hoy)

    for individuo in poblacion:
        for idx, semilla in enumerate(SEMILLAS):
            cantidad_toneladas = ((individuo[idx]/area) * toneladas[idx])
            precio = float(precios_dict.get(semilla))
            obj = funcionObjetivo(cantidad_toneladas, precio)
        objetivos.append(obj)
    return objetivos

def red_neuronal(individuo, depto, lon, lat):
    # Uno con datos del suelo
    df_suelo = pd.read_csv("Recuperacion_de_datos/Suelos/suelo_promedio.csv")
    df_suelo = df_suelo[df_suelo['departamento_nombre'] == depto]

    # Uno con datos predecidos del clima
    df_predicciones_clima = predecir_datos_clima(depto)

    # Creo el dataframe final para pasar a la red neuronal
    df_final = pd.DataFrame()
    filas = []
        
    for idx, area in enumerate(individuo):
        anio = 2025 if idx < 4 else 2026

        # Convertir columnas de suelo y clima a float
        suelo_dict = {k: (float(v) if k != 'departamento_nombre' and k != 'coords' else v) for k, v in df_suelo.iloc[0].to_dict().items()}
        clima_dict = {k: float(v) for k, v in df_predicciones_clima.iloc[0].to_dict().items()}

        fila = {
            'superficie_sembrada_ha': float(area),
            **suelo_dict,
            **clima_dict,
            'cultivo_nombre': int(cultivo_a_entero[SEMILLAS[idx]]),
            'anio': int(anio)
        }
        filas.append(fila)

    df_final = pd.DataFrame(filas)

    cols = ['cultivo_nombre', 'anio', 'organic_carbon', 'ph', 'clay', 'silt', 'sand', 
                    'temperatura_media_C_1', 'temperatura_media_C_2', 'temperatura_media_C_3', 'temperatura_media_C_4', 
                    'temperatura_media_C_5', 'temperatura_media_C_6', 'temperatura_media_C_7', 'temperatura_media_C_8', 
                    'temperatura_media_C_9', 'temperatura_media_C_10', 'temperatura_media_C_11', 'temperatura_media_C_12', 
                    'temperatura_media_C_13', 'temperatura_media_C_14', 'humedad_relativa_%_1', 'humedad_relativa_%_2', 
                    'humedad_relativa_%_3', 'humedad_relativa_%_4', 'humedad_relativa_%_5', 'humedad_relativa_%_6', 
                    'humedad_relativa_%_7', 'humedad_relativa_%_8', 'humedad_relativa_%_9', 'humedad_relativa_%_10', 
                    'humedad_relativa_%_11', 'humedad_relativa_%_12', 'humedad_relativa_%_13', 'humedad_relativa_%_14', 
                    'velocidad_viento_m_s_1', 'velocidad_viento_m_s_2', 'velocidad_viento_m_s_3', 'velocidad_viento_m_s_4', 
                    'velocidad_viento_m_s_5', 'velocidad_viento_m_s_6', 'velocidad_viento_m_s_7', 'velocidad_viento_m_s_8', 
                    'velocidad_viento_m_s_9', 'velocidad_viento_m_s_10', 'velocidad_viento_m_s_11', 'velocidad_viento_m_s_12', 
                    'velocidad_viento_m_s_13', 'velocidad_viento_m_s_14', 'precipitacion_mm_mes_1', 'precipitacion_mm_mes_2', 
                    'precipitacion_mm_mes_3', 'precipitacion_mm_mes_4', 'precipitacion_mm_mes_5', 'precipitacion_mm_mes_6', 
                    'precipitacion_mm_mes_7', 'precipitacion_mm_mes_8', 'precipitacion_mm_mes_9', 'precipitacion_mm_mes_10', 
                    'precipitacion_mm_mes_11', 'precipitacion_mm_mes_12', 'precipitacion_mm_mes_13', 'precipitacion_mm_mes_14', 
                    'superficie_sembrada_ha']
    df_final = df_final[cols]

    predicciones_toneladas = utilizar_GBM(df_final)
    return predicciones_toneladas

## FITNESS ORIGINAL
def calculadorFitness(objetivos):                   
    fitness = []
    suma = sum(objetivos)
    for fo in objetivos:
        fit = fo / suma
        fitness.append(fit)
    return fitness

# metodo correccion original
def metodo_correccion(individuo, precios, toneladas, area_ha):
    cultivos = sum(1 for x in individuo if x != 0)
    if cultivos > 2:
        total = 0
        for x in range(len(individuo)):
            if individuo[x] < area_ha*0.05:
                total = individuo[x]
                individuo[x] = 0
        individuo_modif = []
        for i in range(len(individuo)):
            valor = individuo[i]+(total/cultivos)
            individuo_modif.append(valor)
        return individuo_modif
    else:
        return individuo
        

def calculadorEstadisticos(poblacion, objetivos):
    max_objetivos = max(objetivos)
    min_objetivos = min(objetivos)
    mejor_cromosoma = poblacion[objetivos.index(max_objetivos)]
    avg_objetivos = round((sum(objetivos)/len(objetivos)),4)
    return [max_objetivos,min_objetivos, avg_objetivos, mejor_cromosoma] 

# Crossover
def crossover1Punto(padre, madre, maximo):         
    puntoCorte = random.randint(1, len(padre)-1)
    h1 = padre[:puntoCorte] + madre[puntoCorte:]
    h2 = madre[:puntoCorte] + padre[puntoCorte:]
    h1 = normalizar(h1, maximo)
    h2 = normalizar(h2, maximo)
    return h1, h2

def normalizar(individuo, maximo):
    s = sum(individuo)
    return [(x/s) * maximo for x in individuo]

# Mutaciones
def mutacionInvertida(poblacion, probMutacion):         
    for i in range(len(poblacion)):
        if random.random() < probMutacion:
            individuo = poblacion[i]
            pos1 = random.randint(0, len(individuo) - 1)
            pos2 = random.randint(0, len(individuo) - 1)
            while pos1 == pos2:
                pos2 = random.randint(0, len(individuo) - 1)
            # Ordenar para que pos1 < pos2
            if pos1 > pos2:
                pos1, pos2 = pos2, pos1
            segmento_invertido = individuo[pos1:pos2+1][::-1]
            poblacion[i] = individuo[:pos1] + segmento_invertido + individuo[pos2+1:]
    return poblacion

def mutacionSwap(poblacion, probMutacion):         
    # Se utilizará Swap mutation
    for i in range(len(poblacion)):
        if random.random() < probMutacion:
            individuo = poblacion[i]
            pos1 = random.randint(0, len(individuo) - 1)
            pos2 = random.randint(0, len(individuo) - 1)
            # Ordenar para que pos1 < pos2
            while pos1 == pos2:
                pos2 = random.randint(0, len(individuo) - 1)
            individuo[pos1], individuo[pos2] = individuo[pos2], individuo[pos1]
            poblacion[i] = individuo
    return poblacion

# SELECCION
# Ruleta
def seleccionRuleta(poblacion, fitnessValores, cantidad):
    # Generar acumuladas
    acumuladas = []
    acum = 0
    for fit in fitnessValores:
        acum += fit
        acumuladas.append(acum)
    seleccionados = []
    for _ in range(cantidad):
        probAleatoria = random.random()
        for i, acum in enumerate(acumuladas):
            if probAleatoria <= acum:
                seleccionados.append(poblacion[i])
                break
    return seleccionados

# Torneo
def seleccionTorneo(poblacion, fitnessValores, cantidadIndividuos, cantidadCompetidores):
    ganadores = []
    for j in range(cantidadIndividuos):
        competidores = []
        fitness_competidores = []
        for i in range(cantidadCompetidores):
            indice = random.randint(0, len(poblacion)-1)
            competidores.append(poblacion[indice])
            fitness_competidores.append(fitnessValores[indice])
        ganador = competidores[fitness_competidores.index(max(fitness_competidores))]
        ganadores.append(ganador)
    return ganadores

# CICLOS
# Elitismo
def ciclos_con_elitismo(depto, lat, lon, area_ha, ciclos, prob_crossover, prob_mutacion, cant_individuos, cant_genes, metodo_seleccion, cantidadElitismo, 
                        correccion, cantidadCompetidores=None):
    toneladas = pred_toneladas(area_ha, depto, lon, lat)
    maximos=[]
    minimos=[]
    promedios=[]
    mejores=[]
    
    pob = generarPoblacion(cant_individuos, cant_genes, area_ha) #Poblacion inicial random
    fo = calculadorFuncionObjetivo(pob, toneladas, area_ha)
    fit = calculadorFitness(fo)
    rta = calculadorEstadisticos(pob, fo)

    maximos.append(rta[0])
    minimos.append(rta[1])
    promedios.append(rta[2])
    mejores.append(rta[3])

    for j in range (ciclos):
        elitistas = [] 
        fit_ordenados = sorted(fit, reverse = True)

        for i in range(cantidadElitismo):
            indice = fit.index(fit_ordenados[i])
            elitistas.append(pob[indice])

        if metodo_seleccion == 'r':
            pob_intermedia = seleccionRuleta(pob, fit, cant_individuos - cantidadElitismo)
        else:
            pob_intermedia = seleccionTorneo(pob, fit, cant_individuos - cantidadElitismo, cantidadCompetidores) 
        #print(len(pob_intermedia))

        #REALIZO CROSSOVER Y MUTACION EN LA POBLACION
        for i in range (0,len(pob_intermedia),2):
            padre = pob_intermedia[i]
            madre = pob_intermedia[i+1]
            if random.random() < prob_crossover :
                hijo1, hijo2 = crossover1Punto(padre, madre, area_ha)
                pob_intermedia[i], pob_intermedia[i+1] = hijo1, hijo2
            
        pob_intermedia = mutacionSwap(pob_intermedia, prob_mutacion)
        
        pob = pob_intermedia + elitistas

        if correccion:
            index = fit.index(fit_ordenados[-1])
            precios = obtener_precios()
            pob[index] = metodo_correccion(pob[index], precios, toneladas, area_ha)
        
        fo = calculadorFuncionObjetivo(pob, toneladas, area_ha)
        fit = calculadorFitness(fo)
        rta = calculadorEstadisticos(pob, fo)
        #GUARDAR VALORES NECESARIOS PARA LA GRAFICA
        maximos.append(rta[0])
        minimos.append(rta[1])
        promedios.append(rta[2])
        mejores.append(rta[3])

        suma = [0] * 7
        total = 0.0
        for x in pob:
            suma[0] += x[0]
            suma[1] += x[1]
            suma[2] += x[2]
            suma[3] += x[3]
            suma[4] += x[4]
            suma[5] += x[5]
            suma[6] += x[6]

            total = suma[0] + suma[1] + suma[2] + suma[3] + suma[4] + suma[5] + suma[6]


        print(f"------------------ ITERACION: {j+1} ----------------------------")
        print(f"\n GIRASOL: {mejores[-1][0]} || total: {suma[0]}")
        print(f"\n SOJA: {mejores[-1][1]} || total: {suma[1]}")
        print(f"\n MAIZ: {mejores[-1][2]} || total: {suma[2]}")
        print(f"\n TRIGO: {mejores[-1][3]} || total: {suma[3]}")
        print(f"\n SORGO: {mejores[-1][4]} || total: {suma[4]}")
        print(f"\n CEBADA: {mejores[-1][5]} || total: {suma[5]}")
        print(f"\n MANI: {mejores[-1][6]} || total: {suma[6]}")
        total_ind = mejores[-1][0] + mejores[-1][1] + mejores[-1][2] + mejores[-1][3] + mejores[-1][4] + mejores[-1][5] + mejores[-1][6]
        print(f"\n TOTAL DE HA POBLACIÓN: {total} || TOTAL DE HA INDIVIDUO: {total_ind}")
        print("----------------------------------------------")
        
    return maximos, minimos, promedios, mejores

# Sin elitismo
def ciclos_sin_elitismo(depto, lat, lon, area_ha, ciclos, prob_crossover, prob_mutacion, cantidadIndividuos, cant_genes, metodo_seleccion, 
                        correccion, cantidadCompetidores=None):
    toneladas = pred_toneladas(area_ha, depto, lon, lat)
    maximos=[]
    minimos=[]
    promedios=[]
    mejores=[]
    
    pob = generarPoblacion(cantidadIndividuos, cant_genes, area_ha)
    fo = calculadorFuncionObjetivo(pob, toneladas, area_ha)
    fit = calculadorFitness(fo)
    rta = calculadorEstadisticos(pob, fo)
    
    maximos.append(rta[0])
    minimos.append(rta[1])
    promedios.append(rta[2])
    mejores.append(rta[3])

    for j in range (ciclos):
        if metodo_seleccion == 'r':
            pob = seleccionRuleta(pob, fit, cantidadIndividuos)
        else:
            pob = seleccionTorneo(pob, fit, cantidadIndividuos, cantidadCompetidores) 
        for i in range (0,len(pob),2):
            if i + 1 < len(pob):
                padre = pob[i]
                madre = pob[i+1]
            if random.random() < prob_crossover :
                hijo1, hijo2 = crossover1Punto(padre, madre, area_ha)
                pob[i], pob[i+1] = hijo1, hijo2


        if correccion:
            fit_ordenados = sorted(fit, reverse=True)
            index = fit.index(fit_ordenados[-1])
            precios = obtener_precios()
            pob[index] = metodo_correccion(pob[index], precios, toneladas, area_ha)
        
        pob = mutacionSwap(pob, prob_mutacion)
        fo = calculadorFuncionObjetivo(pob, toneladas, area_ha)
        fit = calculadorFitness(fo)
        rta = calculadorEstadisticos(pob, fo)

        #GUARDAR VALORES NECESARIOS PARA LA GRAFICA
        maximos.append(rta[0])
        minimos.append(rta[1])
        promedios.append(rta[2])
        mejores.append(rta[3])

        suma = [0] * 7
        total = 0.0
        for x in pob:
            suma[0] += x[0]
            suma[1] += x[1]
            suma[2] += x[2]
            suma[3] += x[3]
            suma[4] += x[4]
            suma[5] += x[5]
            suma[6] += x[6]

            total = suma[0] + suma[1] + suma[2] + suma[3] + suma[4] + suma[5] + suma[6]

        print(f"------------------ ITERACION: {j+1} ----------------------------")
        print(f"\n GIRASOL: {mejores[-1][0]} || total: {suma[0]}")
        print(f"\n SOJA: {mejores[-1][1]} || total: {suma[1]}")
        print(f"\n MAIZ: {mejores[-1][2]} || total: {suma[2]}")
        print(f"\n TRIGO: {mejores[-1][3]} || total: {suma[3]}")
        print(f"\n SORGO: {mejores[-1][4]} || total: {suma[4]}")
        print(f"\n CEBADA: {mejores[-1][5]} || total: {suma[5]}")
        print(f"\n MANI: {mejores[-1][6]} || total: {suma[6]}")
        total_ind = mejores[-1][0] + mejores[-1][1] + mejores[-1][2] + mejores[-1][3] + mejores[-1][4] + mejores[-1][5] + mejores[-1][6]
        print(f"\n TOTAL DE HA POBLACIÓN: {total} || TOTAL DE HA INDIVIDUO: {total_ind}")
        print("----------------------------------------------")

    return maximos, minimos, promedios, mejores

def generar_grafico(maximos, minimos, promedios, titulo):
    x = list(range(len(maximos)))

    fig, ax = plt.subplots(figsize=(10, 6)) 

    ax.plot(x, maximos, label='Máximos', marker='o', linestyle='-', color='b', linewidth=1, markersize=2)
    ax.plot(x, minimos, label='Mínimos', marker='o', linestyle='-', color='g', linewidth=1, markersize=2)
    ax.plot(x, promedios, label='Promedios', marker='o', linestyle='-', color='r', linewidth=1, markersize=2)

    ax.set_title('Evolución de la población')
    ax.set_xlabel('Generación', fontsize=12)
    ax.set_ylabel('Función Objetivo', fontsize=12)

    # Ajustar automáticamente el rango según los datos
    ax.set_ylim(min(minimos) * 0.95, max(maximos) * 1.05)
    ax.set_xlim(0, len(maximos) - 1)

    ax.grid(True)
    ax.legend(fontsize=10)

    fig.suptitle(titulo, fontsize=15)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig('Archivos/Graficas/' + titulo.replace(" ", "_") + '.png', dpi=600, bbox_inches="tight")
    plt.show()

def grafico_terreno(cromosoma, titulo):
    
    sizes = [area for area in cromosoma if area > 0]
    labels = [f"{semilla}\n{round(area, 2)} ha" 
              for semilla, area in zip(SEMILLAS, cromosoma) if area > 0]
    colors = plt.cm.Set3(range(len(sizes)))  

    plt.figure(figsize=(8, 6))
    squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.8)
    plt.axis("off")
    plt.title(titulo, fontsize=14)
    plt.tight_layout()
    plt.savefig(f"Archivos/Graficas/{titulo.replace(' ', '_')}.png", dpi=600, bbox_inches="tight")
    plt.show()


def main(depto, lat, lon, area_ha):
    probCrossover = 0.75
    probMutacion = 0.001
    cantidadIndividuos = 10
    cantidadElitismo = 2
    cantidadCompetidores = int(cantidadIndividuos * 0.4)

    cantidadGenes = 7
    maximosPorCiclo = []
    minimosPorCiclo = []
    promediosPorCiclo = []

    while True:
        ciclos = input("\nIngrese la cantidad de ciclos (debe ser un entero): ")
        try:
            ciclos = int(ciclos)
            break
        except ValueError:
            print("Por favor, ingrese un número entero válido.")
    while True:
        seleccion = input("\nIngrese el método de seleccion <r-ruleta t-torneo>: ")
        if seleccion.lower() in ['r', 't']:
            break
        else:
            print("Por favor, ingrese 'r' para ruleta o 't' para torneo.")
    while True:
        elitismo = input("\n¿Quiere usar elitismo? <elitismo: 1-si 0-no> ")
        if elitismo in ['0', '1']:
            elitismo = int(elitismo)
            break
        else:
            print("Por favor, ingrese '1' para sí o '0' para no.")
    while True:
        correccion = input("\n¿Quiere usar metodo correctivo? <metodo correctivo: 1-si 0-no> ")
        if correccion in ['0', '1']:
            correccion = int(correccion)
            break
        else:
            print("Por favor, ingrese '1' para sí o '0' para no.")
    
    
    if elitismo == 1:
        maximosPorCiclo, minimosPorCiclo, promediosPorCiclo, mejores = ciclos_con_elitismo(depto, lat, lon, area_ha, ciclos, probCrossover, probMutacion, 
                                                                                           cantidadIndividuos, cantidadGenes, 
                                                                                           seleccion, 
                                                                                           cantidadElitismo, correccion, cantidadCompetidores)
        if seleccion == 'r':
            titulo = 'Seleccion RULETA ELITISTA - de '+ str(ciclos) + ' ciclos'
        else:
            titulo = 'Seleccion TORNEO ELITISTA - de '+ str(ciclos) + ' ciclos'
        generar_grafico(maximosPorCiclo, minimosPorCiclo, promediosPorCiclo, titulo)
        grafico_terreno(mejores[-1], "Grafico Campo")
        #crear_tabla(maximosPorCiclo, minimosPorCiclo, promediosPorCiclo, mejores, seleccion, elitismo)
    else:
        maximosPorCiclo, minimosPorCiclo, promediosPorCiclo, mejores = ciclos_sin_elitismo(depto, lat, lon, area_ha, ciclos, probCrossover, probMutacion, 
                                                                                           cantidadIndividuos, cantidadGenes, 
                                                                                           seleccion, correccion, cantidadCompetidores)
        if seleccion == 'r':
            titulo = 'Seleccion RULETA - de '+ str(ciclos) + ' ciclos'
        else:
            titulo = 'Seleccion TORNEO - de '+ str(ciclos) + ' ciclos'
        generar_grafico(maximosPorCiclo, minimosPorCiclo, promediosPorCiclo, titulo)
        grafico_terreno(mejores[-1], "Grafico Campo")
        #crear_tabla(maximosPorCiclo, minimosPorCiclo, promediosPorCiclo, mejores, seleccion, elitismo)

    return

if __name__ == "__main__":

    # PROGRAMA PRINCIPAL
    probCrossover = 0.75
    probMutacion = 0.05
    cantidadIndividuos = 10
    cantidadElitismo = 2
    cantidadCompetidores = int(cantidadIndividuos * 0.4)

    cantidadGenes = 7
    maximosPorCiclo = []
    minimosPorCiclo = []
    promediosPorCiclo = []

    latitud = -31.4
    longitud = -64.2
    departamento = "San Nicolás"
    area_ha = 1900

    main(departamento, latitud, longitud, area_ha)
    #verificar_maximo(maximosPorCiclo)
