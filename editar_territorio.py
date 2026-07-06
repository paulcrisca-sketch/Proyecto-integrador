import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Función para cargar los datos del archivo json
def cargar_datos():
    ruta_actual = os.path.dirname(__file__)
    ruta_json = os.path.join(ruta_actual, "datos.json")
    if not os.path.exists(ruta_json) or os.path.getsize(ruta_json) == 0:
        return {}, ruta_json
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f), ruta_json

# Función para guardar los cambios en el archivo json
def guardar_datos(datos, ruta_json):
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# Función para gestionar las parroquias y barrios
def abrir_ventana_territorios(ventana_principal, callback_actualizar):
    datos, ruta_json = cargar_datos()

    top = tk.Toplevel(ventana_principal)
    top.title("Gestor de Territorios e Indicadores Socioeconómicos")
    top.geometry("780x560")
    top.configure(bg="#F4F6F7")
    top.grab_set()

    parr_seleccionada = tk.StringVar()

    # Panel izquierdo para configuración de parroquia y pesos
    frame_izq = tk.LabelFrame(top, text=" Configuración de la Parroquia ", bg="#F4F6F7", font=("Helvetica", 9, "bold"))
    frame_izq.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    tk.Label(frame_izq, text="Seleccione Parroquia:", bg="#F4F6F7").pack(anchor="w", padx=10, pady=5)
    combo_parr = ttk.Combobox(frame_izq, textvariable=parr_seleccionada, values=list(datos.keys()), state="readonly")
    combo_parr.pack(fill="x", padx=10, pady=5)

    frame_pesos = tk.LabelFrame(frame_izq, text=" Pesos de Priorización (Suman 1.0) ", bg="#F4F6F7")
    frame_pesos.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_pesos, text="Seguridad (W1):", bg="#F4F6F7").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    ent_w1 = tk.Entry(frame_pesos, width=10)
    ent_w1.grid(row=0, column=1, padx=5, pady=2)

    tk.Label(frame_pesos, text="Población (W2):", bg="#F4F6F7").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    ent_w2 = tk.Entry(frame_pesos, width=10)
    ent_w2.grid(row=1, column=1, padx=5, pady=2)

    tk.Label(frame_pesos, text="Viabilidad (W3):", bg="#F4F6F7").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    ent_w3 = tk.Entry(frame_pesos, width=10)
    ent_w3.grid(row=2, column=1, padx=5, pady=2)

    # Carga los datos de la parroquia seleccionada en los campos
    def cargar_datos_parroquia(evento):
        p = parr_seleccionada.get()
        if p in datos:
            pesos = datos[p].get("pesos", [0.34, 0.33, 0.33])
            ent_w1.delete(0, tk.END)
            ent_w1.insert(0, str(pesos[0]))
            ent_w2.delete(0, tk.END)
            ent_w2.insert(0, str(pesos[1]))
            ent_w3.delete(0, tk.END)
            ent_w3.insert(0, str(pesos[2]))
            actualizar_lista_barrios()

    combo_parr.bind("<<ComboboxSelected>>", cargar_datos_parroquia)

    # Guarda los pesos definidos para la parroquia
    def guardar_configuracion():
        p = parr_seleccionada.get()
        if not p:
            messagebox.showwarning("Aviso", "Seleccione una parroquia.")
            return
        try:
            w1, w2, w3 = float(ent_w1.get()), float(ent_w2.get()), float(ent_w3.get())
            if round(w1 + w2 + w3, 2) != 1.0:
                messagebox.showerror("Error", "La suma de los pesos debe ser igual a 1.0")
                return

            datos[p]["pesos"] = [w1, w2, w3]
            guardar_datos(datos, ruta_json)
            messagebox.showinfo("Éxito", "Pesos guardados correctamente.")
            callback_actualizar()
        except ValueError:
            messagebox.showerror("Error", "Ingrese solo números en los pesos.")

    # Elimina la parroquia seleccionada
    def eliminar_parroquia():
        p = parr_seleccionada.get()
        if not p:
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar la parroquia '{p}'?"):
            del datos[p]
            guardar_datos(datos, ruta_json)
            combo_parr["values"] = list(datos.keys())
            parr_seleccionada.set("")
            actualizar_lista_barrios()
            callback_actualizar()

    frame_btn_p = tk.Frame(frame_izq, bg="#F4F6F7")
    frame_btn_p.pack(pady=10)
    tk.Button(frame_btn_p, text="Guardar Pesos", command=guardar_configuracion, bg="#2B6CB0", fg="white", font=("Helvetica", 9, "bold")).pack(side="left", padx=5)
    tk.Button(frame_btn_p, text="Eliminar", command=eliminar_parroquia, bg="#C53030", fg="white").pack(side="left", padx=5)

    # Seccion para añadir una nueva parroquia
    tk.Label(frame_izq, text="Nueva Parroquia:", bg="#F4F6F7").pack(anchor="w", padx=10)
    ent_nueva_p = tk.Entry(frame_izq)
    ent_nueva_p.pack(fill="x", padx=10, pady=5)

    def agregar_parroquia():
        nombre_nuevo = ent_nueva_p.get().strip()
        if not nombre_nuevo or nombre_nuevo in datos:
            return
        datos[nombre_nuevo] = {"pesos": [0.34, 0.33, 0.33], "barrios": {}}
        guardar_datos(datos, ruta_json)
        combo_parr["values"] = list(datos.keys())
        ent_nueva_p.delete(0, tk.END)

    tk.Button(frame_izq, text="Añadir Parroquia", command=agregar_parroquia, bg="#4A5568", fg="white").pack(pady=5)

    # Panel derecho para la gestión de barrios
    frame_der = tk.LabelFrame(top, text=" Barrios Asociados ", bg="#F4F6F7", font=("Helvetica", 9, "bold"))
    frame_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    lista_barrios = tk.Listbox(frame_der, height=12)
    lista_barrios.pack(fill="both", expand=True, padx=10, pady=5)

    # Refresca la lista de barrios en la interfaz
    def actualizar_lista_barrios():
        lista_barrios.delete(0, tk.END)
        p = parr_seleccionada.get()
        if p in datos and "barrios" in datos[p]:
            for nombre_barrio in datos[p]["barrios"].keys():
                lista_barrios.insert(tk.END, nombre_barrio)

    tk.Label(frame_der, text="Nombre Barrio:", bg="#F4F6F7").pack(anchor="w", padx=10)
    ent_barrio = tk.Entry(frame_der)
    ent_barrio.pack(fill="x", padx=10, pady=5)

    # Añade un nuevo barrio a la parroquia seleccionada
    def agregar_barrio():
        p = parr_seleccionada.get()
        nombre_barrio = ent_barrio.get().strip()
        if not p or not nombre_barrio or nombre_barrio in datos[p]["barrios"]:
            return
        datos[p]["barrios"][nombre_barrio] = []
        guardar_datos(datos, ruta_json)
        actualizar_lista_barrios()
        ent_barrio.delete(0, tk.END)

    frame_btn_b = tk.Frame(frame_der, bg="#F4F6F7")
    frame_btn_b.pack(fill="x", padx=10, pady=5)
    tk.Button(frame_btn_b, text="Añadir Barrio", command=agregar_barrio, bg="#2F855A", fg="white").pack(side="left", padx=2)