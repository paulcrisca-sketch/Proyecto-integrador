import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Variables y constantes del programa
NOMBRE_ARCHIVO = "datos.json"
CRITERIOS = ["Seguridad", "Población", "Viabilidad"] # Etiquetas del vector de notas
NUM_CRITERIOS = len(CRITERIOS) # Cantidad de criterios

# Funciones de persistencia de datos
def cargar_datos():
    # Lee el archivo json y retorna los datos almacenados
    ruta_actual = os.path.dirname(__file__)
    ruta_json = os.path.join(ruta_actual, NOMBRE_ARCHIVO)
    if not os.path.exists(ruta_json) or os.path.getsize(ruta_json) == 0:
        return {}, ruta_json
    with open(ruta_json, "r", encoding="utf-8") as f:
        try:
            return json.load(f), ruta_json
        except json.JSONDecodeError:
            return {}, ruta_json

def guardar_datos(datos, ruta_json):
    # Guarda la estructura completa en el archivo json
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# Estructura del proyecto
def crear_estructura_proyecto(nombre, costo, vector_notas, id_registro):
    # Crea un diccionario con los datos del proyecto
    return {
        "nombre": nombre,
        "costo": costo,
        "notas": vector_notas, # Vector con tres notas
        "id_registro": id_registro,
    }

# Operaciones sobre vectores
def suma_recursiva_vector(vector, indice=0):
    # Suma los elementos del vector usando recursividad
    if indice == len(vector):
        return 0.0
    return vector[indice] + suma_recursiva_vector(vector, indice + 1)

def promedio_vector(vector):
    # Calcula el promedio de los elementos del vector
    if not vector:
        return 0.0
    return suma_recursiva_vector(vector) / len(vector)

# Operaciones sobre matrices
def construir_matriz_evaluaciones(datos):
    # Construye una matriz con los datos de todos los proyectos
    matriz = []
    for parroquia, contenido in datos.items():
        for barrio, lista_proyectos in contenido.get("barrios", {}).items():
            for proyecto in lista_proyectos:
                vector_notas = proyecto["notas"]
                fila = [proyecto["nombre"]] + vector_notas + [promedio_vector(vector_notas)]
                matriz.append(fila)
    return matriz

def obtener_ranking(datos):
    # Ordena la matriz por promedio de forma descendente
    matriz = construir_matriz_evaluaciones(datos)
    matriz_ordenada = sorted(matriz, key=lambda fila: fila[-1], reverse=True)
    return matriz_ordenada

# Ventana de edición
def abrir_ventana_proyectos(ventana_principal, callback_actualizar):
    datos, ruta_json = cargar_datos()

    top = tk.Toplevel(ventana_principal)
    top.title("Editor de Proyectos y Criterios Técnicos")
    top.geometry("560x600")
    top.configure(bg="#F4F6F7")
    top.grab_set()

    # Selectores
    frame_combos = tk.Frame(top, bg="#F4F6F7")
    frame_combos.pack(pady=12, padx=15, fill="x")

    tk.Label(frame_combos, text="Parroquia:", bg="#F4F6F7").grid(row=0, column=0, sticky="w", pady=4)
    combo_p = ttk.Combobox(frame_combos, state="readonly", values=list(datos.keys()))
    combo_p.grid(row=0, column=1, sticky="ew", pady=4)

    tk.Label(frame_combos, text="Barrio:", bg="#F4F6F7").grid(row=1, column=0, sticky="w", pady=4)
    combo_b = ttk.Combobox(frame_combos, state="readonly")
    combo_b.grid(row=1, column=1, sticky="ew", pady=4)

    tk.Label(frame_combos, text="Editar Existente:", bg="#F4F6F7").grid(row=2, column=0, sticky="w", pady=4)
    combo_proy = ttk.Combobox(frame_combos, state="readonly")
    combo_proy.grid(row=2, column=1, sticky="ew", pady=4)

    frame_combos.columnconfigure(1, weight=1)

    # Formulario
    frame_edit = tk.LabelFrame(top, text=" Parámetros Técnicos ", bg="#F4F6F7", font=("Helvetica", 9, "bold"))
    frame_edit.pack(pady=10, padx=15, fill="both", expand=True)

    tk.Label(frame_edit, text="Nombre:", bg="#F4F6F7").grid(row=0, column=0, sticky="w", padx=10, pady=8)
    ent_nombre = tk.Entry(frame_edit, width=32)
    ent_nombre.grid(row=0, column=1, padx=10, pady=8, sticky="w")

    tk.Label(frame_edit, text="Costo:", bg="#F4F6F7").grid(row=1, column=0, sticky="w", padx=10, pady=8)
    ent_costo = tk.Entry(frame_edit, width=16)
    ent_costo.grid(row=1, column=1, padx=10, pady=8, sticky="w")

    entradas_notas = []
    fila_inicial = 2
    for i, criterio in enumerate(CRITERIOS):
        tk.Label(frame_edit, text=f"Nota {criterio}:", bg="#F4F6F7").grid(row=fila_inicial + i, column=0, sticky="w", padx=10, pady=8)
        ent = tk.Entry(frame_edit, width=10)
        ent.grid(row=fila_inicial + i, column=1, padx=10, pady=8, sticky="w")
        entradas_notas.append(ent)

    lbl_promedio = tk.Label(frame_edit, text="Promedio", bg="#F4F6F7", font=("Helvetica", 9, "bold"))
    lbl_promedio.grid(row=fila_inicial + NUM_CRITERIOS, column=0, columnspan=2, pady=10)

    def actualizar_promedio():
        try:
            vector_actual = [float(e.get()) for e in entradas_notas]
            lbl_promedio.config(text=f"Promedio: {promedio_vector(vector_actual):.2f}")
        except ValueError:
            lbl_promedio.config(text="Promedio")

    for e in entradas_notas:
        e.bind("<KeyRelease>", lambda ev: actualizar_promedio())

    # Controladores de eventos
    def al_cambiar_parroquia(e):
        p = combo_p.get()
        if p in datos and "barrios" in datos[p]:
            combo_b["values"] = list(datos[p]["barrios"].keys())
        else:
            combo_b["values"] = []
        combo_b.set("")
        combo_proy.set("")
        limpiar_formulario()

    def al_cambiar_barrio(e):
        p, b = combo_p.get(), combo_b.get()
        if p in datos and b in datos[p]["barrios"]:
            combo_proy["values"] = [proy["nombre"] for proy in datos[p]["barrios"][b]]
        else:
            combo_proy["values"] = []
        combo_proy.set("")
        limpiar_formulario()

    def al_cargar_proyecto(e):
        p, b, np = combo_p.get(), combo_b.get(), combo_proy.get()
        if not (p and b and np):
            return
        for proy in datos[p]["barrios"][b]:
            if proy["nombre"] == np:
                limpiar_formulario()
                ent_nombre.insert(0, str(proy["nombre"]))
                ent_costo.insert(0, str(proy["costo"]))
                for i, ent in enumerate(entradas_notas):
                    ent.insert(0, str(proy["notas"][i]))
                actualizar_promedio()
                break

    def limpiar_formulario():
        ent_nombre.delete(0, tk.END)
        ent_costo.delete(0, tk.END)
        for ent in entradas_notas:
            ent.delete(0, tk.END)
        lbl_promedio.config(text="Promedio")

    combo_p.bind("<<ComboboxSelected>>", al_cambiar_parroquia)
    combo_b.bind("<<ComboboxSelected>>", al_cambiar_barrio)
    combo_proy.bind("<<ComboboxSelected>>", al_cargar_proyecto)

    # Acciones de botones
    def guardar_accion():
        p, b, np = combo_p.get(), combo_b.get(), combo_proy.get()
        if not p or not b:
            messagebox.showwarning("Aviso", "Seleccione Parroquia y Barrio.")
            return
        try:
            costo = float(ent_costo.get())
            n_name = ent_nombre.get().strip()
            vector_notas = [float(ent.get()) for ent in entradas_notas]
            if not n_name:
                messagebox.showwarning("Aviso", "Nombre requerido.")
                return
            if np:
                for proy in datos[p]["barrios"][b]:
                    if proy["nombre"] == np:
                        proy["nombre"] = n_name
                        proy["costo"] = costo
                        proy["notas"] = vector_notas
                        break
            else:
                total_global = sum(len(barrio) for parr in datos.values() for barrio in parr.get("barrios", {}).values())
                if p not in datos: datos[p] = {"barrios": {}}
                if b not in datos[p]["barrios"]: datos[p]["barrios"][b] = []
                nuevo_proyecto = crear_estructura_proyecto(n_name, costo, vector_notas, total_global + 1)
                datos[p]["barrios"][b].append(nuevo_proyecto)
            guardar_datos(datos, ruta_json)
            messagebox.showinfo("Éxito", "Proyecto guardado.")
            callback_actualizar()
            top.destroy()
        except ValueError:
            messagebox.showerror("Error", "Valores numéricos inválidos.")

    def eliminar_accion():
        p, b, np = combo_p.get(), combo_b.get(), combo_proy.get()
        if not (p and b and np): return
        if messagebox.askyesno("Confirmar", "¿Eliminar proyecto?"):
            datos[p]["barrios"][b] = [proy for proy in datos[p]["barrios"][b] if proy["nombre"] != np]
            guardar_datos(datos, ruta_json)
            callback_actualizar()
            top.destroy()

    def ver_ranking_accion():
        # Muestra la matriz de evaluaciones
        ranking = obtener_ranking(datos)
        if not ranking:
            messagebox.showinfo("Ranking", "No hay proyectos.")
            return
        ventana_ranking = tk.Toplevel(top)
        ventana_ranking.title("Ranking")
        ventana_ranking.geometry("480x360")
        columnas = ["Proyecto"] + CRITERIOS + ["Promedio"]
        tree = ttk.Treeview(ventana_ranking, columns=columnas, show="headings")
        for col in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for fila in ranking:
            nombre, *resto = fila
            tree.insert("", tk.END, values=[nombre] + [f"{v:.2f}" for v in resto])

    frame_btns = tk.Frame(top, bg="#F4F6F7")
    frame_btns.pack(fill="x", side="bottom", pady=15)
    tk.Button(frame_btns, text="Guardar", command=guardar_accion).pack(side="left", padx=15)
    tk.Button(frame_btns, text="Ranking", command=ver_ranking_accion).pack(side="left", padx=15)
    tk.Button(frame_btns, text="Eliminar", command=eliminar_accion).pack(side="right", padx=15)

# Punto de entrada
if __name__ == "__main__":
    raiz = tk.Tk()
    raiz.title("Gestor de Proyectos")
    raiz.geometry("300x120")
    def refrescar(): print("Actualizado.")
    tk.Button(raiz, text="Abrir Editor", command=lambda: abrir_ventana_proyectos(raiz, refrescar)).pack(expand=True)
    raiz.mainloop()