import json
import os
import numpy as np


def _cargar_datos():
    ruta_actual = os.path.dirname(__file__)
    ruta_json = os.path.join(ruta_actual, "datos.json")

    if not os.path.exists(ruta_json) or os.path.getsize(ruta_json) == 0:
        return {}

    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def _calcular_puntajes(datos):
    # Calcula el puntaje de cada proyecto multiplicando sus notas por los pesos de la parroquia.
    lista_proyectos = []

    for nombre_parroquia, info_parroquia in datos.items():
        pesos = info_parroquia.get("pesos", [0.34, 0.33, 0.33])

        proyectos_parroquia = []
        for nombre_barrio, proyectos in info_parroquia.get("barrios", {}).items():
            for proyecto in proyectos:
                proyectos_parroquia.append((nombre_barrio, proyecto))

        if not proyectos_parroquia:
            continue

        vector_pesos = np.array(pesos)
        matriz_notas = np.array([proyecto["notas"] for _, proyecto in proyectos_parroquia])
        vector_puntajes = matriz_notas.dot(vector_pesos)

        for (nombre_barrio, proyecto), puntaje in zip(proyectos_parroquia, vector_puntajes):
            lista_proyectos.append({
                "parroquia": nombre_parroquia,
                "barrio": nombre_barrio,
                "nombre": proyecto["nombre"],
                "costo": proyecto["costo"],
                "notas": proyecto["notas"],
                "pesos": pesos,
                "puntaje": round(float(puntaje), 2),
                "id_registro": proyecto.get("id_registro", 99),
            })

    return lista_proyectos


def _clave_orden(proyecto):
    # Criterio de ordenamiento basado en el puntaje del proyecto.
    return proyecto["puntaje"]


# --- Optimización de recursos ---


def _optimizar_seleccion(proyectos, presupuesto):
    # Selecciona la mejor combinación de proyectos usando programación dinámica.
    n = len(proyectos)
    capacidad = int(round(presupuesto))
    if capacidad <= 0 or n == 0:
        return set()

    costos = [max(0, int(round(p["costo"]))) for p in proyectos]
    valores = [p["puntaje"] for p in proyectos]

    dp = [[0.0] * (capacidad + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        costo_i = costos[i - 1]
        valor_i = valores[i - 1]
        fila_prev = dp[i - 1]
        fila_actual = dp[i]
        for c in range(capacidad + 1):
            mejor = fila_prev[c]
            if costo_i <= c:
                candidato = fila_prev[c - costo_i] + valor_i
                if candidato > mejor:
                    mejor = candidato
            fila_actual[c] = mejor

    seleccionados = set()
    c = capacidad
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            seleccionados.add(i - 1)
            c -= costos[i - 1]

    return seleccionados


def _aprobar_greedy(proyectos, presupuesto):
    # Aprueba proyectos en orden secuencial de mayor a menor puntaje.
    seleccionados = set()
    restante = presupuesto

    for i, proyecto in enumerate(proyectos):
        if proyecto["costo"] <= restante:
            seleccionados.add(i)
            restante -= proyecto["costo"]

    return seleccionados


def procesar_priorizacion(presupuesto_disponible, usar_mochila=True):
    # Calculates, ordena y asigna el estado de aprobado o rechazado a los proyectos.
    datos = _cargar_datos()
    lista_proyectos = _calcular_puntajes(datos)

    if not lista_proyectos:
        return []

    proyectos_ordenados = sorted(lista_proyectos, key=_clave_orden, reverse=True)

    if usar_mochila:
        indices_aprobados = _optimizar_seleccion(proyectos_ordenados, presupuesto_disponible)
    else:
        indices_aprobados = _aprobar_greedy(proyectos_ordenados, presupuesto_disponible)

    for i, proyecto in enumerate(proyectos_ordenados):
        if i in indices_aprobados:
            proyecto["estado"] = "Aprobado"
        else:
            proyecto["estado"] = "Rechazado"

    return proyectos_ordenados


# --- Simulaciones y escenarios ---


def generar_curva_presupuesto(presupuesto_referencia, num_puntos=12):
    # Genera una lista de escenarios simulando diferentes montos de presupuesto.
    presupuesto_maximo = max(presupuesto_referencia * 1.5, 1.0)
    paso = presupuesto_maximo / num_puntos

    resumenes = []
    presupuesto_actual = 0.0
    while presupuesto_actual <= presupuesto_maximo:
        resultados = procesar_priorizacion(presupuesto_actual)
        aprobados = [p for p in resultados if p["estado"] == "Aprobado"]

        cantidad_aprobados = len(aprobados)

        vector_puntajes_aprobados = np.array([p["puntaje"] for p in aprobados])
        vector_costos_aprobados = np.array([p["costo"] for p in aprobados])

        if cantidad_aprobados > 0:
            puntaje_total = float(np.sum(vector_puntajes_aprobados))
            puntaje_promedio = float(np.mean(vector_puntajes_aprobados))
            invertido = float(np.sum(vector_costos_aprobados))
        else:
            puntaje_total = 0.0
            puntaje_promedio = None
            invertido = 0.0

        if puntaje_promedio is None:
            puntaje_promedio_final = None
        else:
            puntaje_promedio_final = round(puntaje_promedio, 2)

        resumenes.append({
            "presupuesto": presupuesto_actual,
            "aprobados": cantidad_aprobados,
            "invertido": invertido,
            "puntaje_total": round(puntaje_total, 2),
            "puntaje_promedio": puntaje_promedio_final,
        })

        presupuesto_actual += paso
        
    return resumenes


def listar_parroquias():
    # Devuelve los nombres de todas las parroquias disponibles.
    datos = _cargar_datos()
    return sorted(datos.keys())


def obtener_proyectos_parroquia(nombre_parroquia):
    # Devuelve los proyectos pertenecientes a una parroquia específica.
    datos = _cargar_datos()
    info_parroquia = datos.get(nombre_parroquia, {})

    proyectos = []
    for nombre_barrio, lista_proyectos in info_parroquia.get("barrios", {}).items():
        for proyecto in lista_proyectos:
            proyectos.append({
                "barrio": nombre_barrio,
                "nombre": proyecto["nombre"],
                "notes": proyecto["notas"],
            })

    return proyectos


def _clave_puntaje_simulado(item):
    # Criterio de ordenamiento para los resultados simulados.
    return item["puntaje"]


def simular_con_pesos(nombre_parroquia, peso_seguridad, peso_poblacion, peso_viabilidad):
    # Calcula puntajes de manera temporal usando pesos de prueba para simulación.
    proyectos = obtener_proyectos_parroquia(nombre_parroquia)
    vector_pesos_prueba = np.array([peso_seguridad, peso_poblacion, peso_viabilidad])

    resultados = []
    for proyecto in proyectos:
        vector_notas = np.array(proyecto["notes"])
        puntaje_simulado = float(vector_notas.dot(vector_pesos_prueba))
        resultados.append({
            "nombre": proyecto["nombre"],
            "barrio": proyecto["barrio"],
            "puntaje": round(puntaje_simulado, 2),
        })

    return sorted(resultados, key=_clave_puntaje_simulado, reverse=True)