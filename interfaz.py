import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import codigo
import editar_territorio
import editar_proyecto

# Guarda el último resultado calculado para no recalcular innecesariamente
resultados_actual = []

# Recuerda si cada columna está en orden ascendente o descendente
orden_columnas = {}

# Nombres internos y títulos visibles de cada columna de la tabla
columnas = ("parr", "barrio", "proy", "notas", "pesos", "puntaje", "costo", "estado")
titulos_columnas = {
    "parr": "Parroquia",
    "barrio": "Barrio",
    "proy": "Proyecto",
    "notas": "Notas [Seg, Pob, Via]",
    "pesos": "Pesos W",
    "puntaje": "Puntaje Final",
    "costo": "Costo Requerido",
    "estado": "Estado",
}

# Ordenar tabla al hacer clic en un encabezado
def convertir_a_numero(texto):
    # Convierte el texto de una celda a número para ordenarla
    texto_limpio = texto.replace("$", "").replace(",", "")
    try:
        return float(texto_limpio)
    except ValueError:
        return texto.lower()

def ordenar_columna(columna):
    orden_descendente = orden_columnas.get(columna, False)
    filas = []
    for fila_id in tabla.get_children(""):
        valor_texto = tabla.set(fila_id, columna)
        filas.append((convertir_a_numero(valor_texto), fila_id))
    filas.sort(reverse=orden_descendente)
    posicion = 0
    for valor, fila_id in filas:
        tabla.move(fila_id, "", posicion)
        posicion += 1
    orden_columnas[columna] = not orden_descendente

def clic_en_encabezado(evento):
    region = tabla.identify_region(evento.x, evento.y)
    if region != "heading":
        return
    columna_id = tabla.identify_column(evento.x)
    indice = int(columna_id.replace("#", "")) - 1
    if 0 <= indice < len(columnas):
        ordenar_columna(columnas[indice])

# Tabla y filtro por parroquia
def renderizar_tabla(resultados, filtro_parroquia):
    for fila in tabla.get_children():
        tabla.delete(fila)
    for proyecto in resultados:
        if filtro_parroquia != "Todas" and proyecto["parroquia"] != filtro_parroquia:
            continue
        tabla.insert("", "end", values=(
            proyecto["parroquia"],
            proyecto["barrio"],
            proyecto["nombre"],
            f"[{proyecto['notas'][0]}, {proyecto['notas'][1]}, {proyecto['notas'][2]}]",
            f"W: {proyecto['pesos']}",
            f"{proyecto['puntaje']:.2f}",
            f"${proyecto['costo']:,.2f}",
            proyecto["estado"],
        ), tags=(proyecto["estado"],))

def al_cambiar_filtro(evento):
    renderizar_tabla(resultados_actual, combo_filtro.get())

# Cálculo principal reactivo al slider
def actualizar_tabla_reactiva(valor_slider=None):
    global resultados_actual
    presupuesto = var_presupuesto.get()
    resultados_actual = codigo.procesar_priorizacion(presupuesto, usar_mochila=var_usar_mochila.get())
    parroquias_disponibles = set()
    for proyecto in resultados_actual:
        parroquias_disponibles.add(proyecto["parroquia"])
    parroquias_disponibles = sorted(parroquias_disponibles)
    seleccion_previa = combo_filtro.get()
    combo_filtro["values"] = ["Todas"] + parroquias_disponibles
    if seleccion_previa not in combo_filtro["values"]:
        combo_filtro.set("Todas")
    renderizar_tabla(resultados_actual, combo_filtro.get())
    actualizar_resumen(resultados_actual, presupuesto)
    actualizar_graficos(resultados_actual, presupuesto)

def actualizar_resumen(resultados, presupuesto):
    if not resultados:
        lbl_resumen.config(text="Sin proyectos evaluados todavía.")
        return
    vector_puntajes = np.array([p["puntaje"] for p in resultados])
    costos_aprobados = []
    for proyecto in resultados:
        if proyecto["estado"] == "Aprobado":
            costos_aprobados.append(proyecto["costo"])
        else:
            costos_aprobados.append(0.0)
    total_aprobados = int(np.count_nonzero(costos_aprobados))
    monto_invertido = float(np.sum(costos_aprobados))
    saldo_restante = presupuesto - monto_invertido
    puntaje_promedio = float(np.mean(vector_puntajes))
    puntaje_max = float(np.max(vector_puntajes))
    if var_usar_mochila.get():
        modo_texto = "Modo: Mochila (óptimo)"
    else:
        modo_texto = "Modo: Simple (orden hasta agotar presupuesto)"
    lbl_resumen.config(text=(
        f"{modo_texto}   |   "
        f"Aprobados: {total_aprobados}   |   "
        f"Invertido: ${monto_invertido:,.2f}   |   "
        f"Saldo restante: ${saldo_restante:,.2f}   |   "
        f"Puntaje promedio: {puntaje_promedio:.2f}   |   "
        f"Puntaje máximo: {puntaje_max:.2f}"
    ))

def actualizar_graficos(resultados, presupuesto):
    fig.clear()
    if not resultados:
        canvas_graf.draw()
        return
    ax_presupuesto = fig.add_subplot(1, 2, 1)
    ax_puntajes = fig.add_subplot(1, 2, 2)
    costos_aprobados = []
    for proyecto in resultados:
        if proyecto["estado"] == "Aprobado":
            costos_aprobados.append(proyecto["costo"])
        else:
            costos_aprobados.append(0.0)
    invertido = float(np.sum(costos_aprobados))
    saldo = max(presupuesto - invertido, 0.0)
    ax_presupuesto.bar(["Invertido", "Saldo restante"], [invertido, saldo], color=["#2B6CB0", "#A0AEC0"])
    ax_presupuesto.set_title("Uso del presupuesto", fontsize=9)
    ax_presupuesto.tick_params(labelsize=8)
    nombres = []
    puntajes = []
    colores = []
    for proyecto in resultados:
        nombres.append(proyecto["nombre"][:14])
        puntajes.append(proyecto["puntaje"])
        if proyecto["estado"] == "Aprobado":
            colores.append("#2F855A")
        else:
            colores.append("#C53030")
    ax_puntajes.barh(nombres, puntajes, color=colores)
    ax_puntajes.set_title("Puntaje por proyecto", fontsize=9)
    ax_puntajes.invert_yaxis()
    ax_puntajes.tick_params(labelsize=7)
    fig.tight_layout()
    canvas_graf.draw()

# Botones que abren otros módulos
def abrir_modulo_territorios():
    editar_territorio.abrir_ventana_territorios(root, actualizar_tabla_reactiva)

def abrir_modulo_proyectos():
    editar_proyecto.abrir_ventana_proyectos(root, actualizar_tabla_reactiva)

# Ventana principal
root = tk.Tk()
root.title("Dashboard Inteligente de Priorización")
root.geometry("1150x780")
root.configure(bg="#E2E8F0")

# Controla si la tabla usa la mochila u optimización simple
var_usar_mochila = tk.BooleanVar(value=True)

frame_header = tk.Frame(root, bg="#1A365D", height=60)
frame_header.pack(fill="x")
tk.Label(frame_header, text="SISTEMA INTELIGENTE DE PRIORIZACIÓN", fg="white", bg="#1A365D", font=("Helvetica", 14, "bold")).pack(pady=10)

frame_ctrl = tk.Frame(root, bg="#E2E8F0")
frame_ctrl.pack(fill="x", padx=20, pady=10)

var_presupuesto = tk.DoubleVar(value=50000)
tk.Label(frame_ctrl, text="Presupuesto ($):", bg="#E2E8F0").pack(side="left")

slider_presupuesto = tk.Scale(frame_ctrl, from_=0, to=200000, orient="horizontal", variable=var_presupuesto, command=actualizar_tabla_reactiva, length=380, resolution=1000)
slider_presupuesto.pack(side="left", padx=15)

tk.Checkbutton(frame_ctrl, text="Usar optimización (mochila)", variable=var_usar_mochila, command=actualizar_tabla_reactiva, bg="#E2E8F0", font=("Helvetica", 9)).pack(side="left", padx=10)

tk.Label(frame_ctrl, text="Filtrar Parroquia:", bg="#E2E8F0").pack(side="left", padx=(20, 5))
combo_filtro = ttk.Combobox(frame_ctrl, values=["Todas"], state="readonly", width=18)
combo_filtro.set("Todas")
combo_filtro.pack(side="left")
combo_filtro.bind("<<ComboboxSelected>>", al_cambiar_filtro)

tk.Button(frame_ctrl, text="Módulo Territorios / Pesos", command=abrir_modulo_territorios, bg="#4A5568", fg="white").pack(side="right", padx=5)
tk.Button(frame_ctrl, text="Gestionar Fichas Proyectos", command=abrir_modulo_proyectos, bg="#4A5568", fg="white").pack(side="right", padx=5)

# Tabla
frame_tabla = tk.Frame(root)
frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)

tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
for nombre_columna in columnas:
    tabla.heading(nombre_columna, text=titulos_columnas[nombre_columna])
    tabla.column(nombre_columna, width=120, anchor="center")

tabla.bind("<Button-1>", clic_en_encabezado)
tabla.tag_configure("Aprobado", background="#DCFCE7")
tabla.tag_configure("Rechazado", background="#FEE2E2")

scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
tabla.configure(yscrollcommand=scroll.set)
tabla.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

# Gráficos
frame_graficos = tk.LabelFrame(root, text=" Panel Visual ", bg="#E2E8F0", font=("Helvetica", 9, "bold"))
frame_graficos.pack(fill="x", padx=20, pady=(0, 10))

fig = Figure(figsize=(10.5, 3.2), dpi=100)
canvas_graf = FigureCanvasTkAgg(fig, master=frame_graficos)
canvas_graf.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

# Resumen
frame_resumen = tk.Frame(root, bg="#1A365D")
frame_resumen.pack(fill="x", side="bottom")
lbl_resumen = tk.Label(frame_resumen, text="", fg="white", bg="#1A365D", font=("Helvetica", 9, "bold"))
lbl_resumen.pack(pady=8)

root.after(300, actualizar_tabla_reactiva)
root.mainloop()