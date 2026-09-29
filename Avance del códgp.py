import streamlit as st
import networkx as nx
import random
import streamlit.components.v1 as componentes
from pyvis.network import Network
import tempfile
import os

# Configuración de página
st.set_page_config(
    page_title="Flujo máximo - Ford Fulkerson",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Algoritmo de Ford Fulkerson & Corte mínimo")
st.markdown("Aplicación interactiva paso a paso para el análisis de redes de flujo.")

# --- INICIALIZACIÓN DEL ESTADO ---
if "numero_nodos" not in st.session_state:
    st.session_state.numero_nodos = 8
if "aristas" not in st.session_state:
    st.session_state.aristas = []
if "fuentes" not in st.session_state:
    st.session_state.fuentes = []
if "sumideros" not in st.session_state:
    st.session_state.sumideros = []
if "ficticios_creados" not in st.session_state:
    st.session_state.ficticios_creados = False
if "historial" not in st.session_state:
    st.session_state.historial = []
if "paso_actual" not in st.session_state:
    st.session_state.paso_actual = 0
if "valor_flujo_maximo" not in st.session_state:
    st.session_state.valor_flujo_maximo = 0

# --- FUNCIONES AUXILIARES ---

def tiene_ciclos(num_nodos, aristas):
    """Verifica si el grafo contiene ciclos directos usando DFS."""
    grafo = nx.DiGraph()
    grafo.add_nodes_from(range(num_nodos))
    for u, v, c in aristas:
        grafo.add_edge(u, v)
    try:
        ciclos = list(nx.simple_cycles(grafo))
        return len(ciclos) > 0, ciclos
    except:
        return False, []

def generar_dag_aleatorio(num_nodos, probabilidad_arista=0.35, cap_max=20):
    """Genera un grafo dirigido acíclico (DAG) aleatorio con capacidades."""
    aristas = []
    # Para evitar ciclos, solo creamos aristas de menor a mayor índice
    for i in range(num_nodos):
        for j in range(i + 1, num_nodos):
            if random.random() < probabilidad_arista:
                cap = random.randint(3, cap_max)
                aristas.append((i, j, cap))
    return aristas

def ejecutar_ford_fulkerson_pasos(num_nodos, aristas, fuente, sumidero):
    """Ejecuta el algoritmo de Ford-Fulkerson paso a paso guardando el historial."""
    # Matriz de capacidades y flujos
    capacidad = {}
    flujo = {}
    nodos = list(range(num_nodos))
    
    for u in nodos:
        for v in nodos:
            capacidad[(u, v)] = 0
            flujo[(u, v)] = 0
            
    adyacencia = {i: set() for i in nodos}
    for u, v, c in aristas:
        capacidad[(u, v)] = c
        adyacencia[u].add(v)
        adyacencia[v].add(u) # Red residual

    historial = []
    
    # Estado inicial (Step 0)
    historial.append({
        "paso": 0,
        "camino": [],
        "cuello_botella": 0,
        "flujo": {k: v for k, v in flujo.items() if capacidad[k] > 0 or capacidad[(k[1], k[0])] > 0},
        "etiquetas": {fuente: ("-", "∞")},
        "flujo_total": 0,
        "mensaje": "Estado inicial: Flujo cero en todas las aristas."
    })

    flujo_total = 0
    iteracion = 1

    while True:
        # Búsqueda de camino aumentante (BFS / Etiquetado)
        etiquetas = {fuente: ("-", float('inf'))}
        padre = {}
        cola = [fuente]
        sumidero_encontrado = False

        while cola and not sumidero_encontrado:
            u = cola.pop(0)
            delta_u = etiquetas[u][1]

            for v in nodos:
                if v not in etiquetas:
                    # Arco directo con capacidad residual
                    residual = capacidad[(u, v)] - flujo[(u, v)]
                    if residual > 0:
                        delta = min(delta_u, residual)
                        etiquetas[v] = (f"{u}+", delta)
                        padre[v] = u
                        cola.append(v)
                        if v == sumidero:
                            sumidero_encontrado = True
                            break
                    # Arco inverso con flujo positivo
                    elif flujo[(v, u)] > 0:
                        delta = min(delta_u, flujo[(v, u)])
                        etiquetas[v] = (f"{u}-", delta)
                        padre[v] = u
                        cola.append(v)
                        if v == sumidero:
                            sumidero_encontrado = True
                            break

        if not sumidero_encontrado:
            # No hay más caminos de aumento. Algoritmo finaliza.
            # Los nodos etiquetados forman el conjunto S y los no etiquetados el conjunto T.
            conjunto_S = set(etiquetas.keys())
            conjunto_T = set(nodos) - conjunto_S
            
            # Calcular capacidad del corte mínimo
            capacidad_corte = 0
            aristas_corte = []
            for u in conjunto_S:
                for v in conjunto_T:
                    if capacidad[(u, v)] > 0:
                        capacidad_corte += capacidad[(u, v)]
                        aristas_corte.append((u, v))

            historial.append({
                "paso": iteracion,
                "camino": [],
                "cuello_botella": 0,
                "flujo": {k: v for k, v in flujo.items() if capacidad[k] > 0 or capacidad[(k[1], k[0])] > 0},
                "etiquetas": etiquetas,
                "flujo_total": flujo_total,
                "finalizado": True,
                "conjunto_S": conjunto_S,
                "conjunto_T": conjunto_T,
                "capacidad_corte": capacidad_corte,
                "aristas_corte": aristas_corte,
                "mensaje": f"¡Flujo Máximo alcanzado! Valor total = {flujo_total}. Se identificó el Corte Mínimo."
            })
            break

        # Reconstruir camino aumentante desde el sumidero
        camino = []
        actual = sumidero
        cuello_botella = etiquetas[sumidero][1]

        while actual != fuente:
            anterior = padre[actual]
            camino.append((anterior, actual))
            actual = anterior
        camino.reverse()

        # Actualizar flujos a lo largo del camino
        for u, v in camino:
            if etiquetas[v][0].endswith("+"):
                flujo[(u, v)] += cuello_botella
            else:
                flujo[(v, u)] -= cuello_botella

        flujo_total += cuello_botella

        historial.append({
            "paso": iteracion,
            "camino": camino,
            "cuello_botella": cuello_botella,
            "flujo": {k: v for k, v in flujo.items() if capacidad[k] > 0 or capacidad[(k[1], k[0])] > 0},
            "etiquetas": etiquetas,
            "flujo_total": flujo_total,
            "finalizado": False,
            "mensaje": f"Iteración {iteracion}: Camino aumentante encontrado {' -> '.join(str(n) for n in [fuente] + [arista[1] for arista in camino])}. Incremento (Δ) = {cuello_botella}."
        })

        iteracion += 1

    return historial

def renderizar_grafo_pyvis(num_nodos, aristas, info_paso_actual, nodo_fuente, nodo_sumidero, nombres_nodos=None):
    """Renderiza el grafo en PyVis con estilos dinámicos para caminos y corte mínimo."""
    red = Network(height="520px", width="100%", directed=True, bgcolor="#f8f9fa", font_color="#000000")
    
    if nombres_nodos is None:
        nombres_nodos = {i: str(i) for i in range(num_nodos)}

    dicc_etiquetas = info_paso_actual.get("etiquetas", {})
    dicc_flujo = info_paso_actual.get("flujo", {})
    aristas_camino = set(info_paso_actual.get("camino", []))
    esta_finalizado = info_paso_actual.get("finalizado", False)
    conjunto_S = info_paso_actual.get("conjunto_S", set())
    aristas_corte = set(info_paso_actual.get("aristas_corte", []))

    # Añadir nodos
    for i in range(num_nodos):
        etiqueta_nodo = f"Nodo {nombres_nodos[i]}"
        if i in dicc_etiquetas:
            tag, delta = dicc_etiquetas[i]
            delta_str = "∞" if delta == float('inf') else str(delta)
            etiqueta_nodo += f"\n({tag}, {delta_str})"

        # Color de nodo según estado
        color = "#97C2FC" # Azul base
        if i == nodo_fuente:
            color = "#2ECC71" # Verde Fuente
        elif i == nodo_sumidero:
            color = "#E74C3C" # Rojo Sumidero
        elif esta_finalizado:
            if i in conjunto_S:
                color = "#F39C12" # Naranja para el conjunto S
            else:
                color = "#3498DB" # Azul para el conjunto T

        red.add_node(
            i, 
            label=etiqueta_nodo, 
            color=color, 
            title=f"Etiqueta: {dicc_etiquetas.get(i, 'Sin etiqueta')}",
            shape="circle",
            size=25
        )

    # Añadir aristas
    for u, v, c in aristas:
        f = dicc_flujo.get((u, v), 0)
        etiqueta_arista = f"{f} / {c}"
        color_arista = "#848484"
        ancho = 2

        # Resaltar camino aumentante actual
        if (u, v) in aristas_camino:
            color_arista = "#F1C40F" # Amarillo resplandeciente
            ancho = 5
        
        # Resaltar aristas del corte mínimo en la iteración final
        if esta_finalizado and (u, v) in aristas_corte:
            color_arista = "#E74C3C" # Rojo
            ancho = 6

        red.add_edge(u, v, label=etiqueta_arista, color=color_arista, width=ancho, arrowStrikethrough=False)

    # Guardar en archivo temporal e inyectar en HTML
    dir_temporal = tempfile.gettempdir()
    ruta = os.path.join(dir_temporal, "graph.html")
    red.save_graph(ruta)
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido_html = f.read()
    return contenido_html


# --- BARRA LATERAL: CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración del grafo")

# 1. Selección del número de nodos n in [7, 16]
numero_nodos = st.sidebar.number_input(
    "Número de Nodos (n ∈ [7, 16]):", 
    min_value=7, 
    max_value=16, 
    value=st.session_state.numero_nodos,
    step=1
)

if numero_nodos != st.session_state.numero_nodos:
    st.session_state.numero_nodos = numero_nodos
    st.session_state.aristas = []
    st.session_state.historial = []
    st.session_state.paso_actual = 0

modo_creacion = st.sidebar.radio("Modo de Creación:", ["Aleatorio", "Manual"])

# 2. Generación Aleatoria
if modo_creacion == "Aleatorio":
    if st.sidebar.button("🎲 Generar Grafo Aleatorio"):
        st.session_state.aristas = generar_dag_aleatorio(numero_nodos)
        st.session_state.historial = []
        st.session_state.paso_actual = 0
        st.session_state.ficticios_creados = False

# 3. Creación Manual
else:
    st.sidebar.subheader("Agregar Arista")
    col1, col2, col3 = st.sidebar.columns(3)
    u_in = col1.number_input("Origen", 0, numero_nodos - 1, 0)
    v_in = col2.number_input("Destino", 0, numero_nodos - 1, 1)
    cap_in = col3.number_input("Capacidad", 1, 100, 10)

    if st.sidebar.button("➕ Añadir Arista"):
        if u_in == v_in:
            st.sidebar.error("No se permiten bucles en el mismo nodo.")
        else:
            # Reemplazar si ya existe la arista
            nuevas_aristas = [e for e in st.session_state.aristas if not (e[0] == u_in and e[1] == v_in)]
            nuevas_aristas.append((u_in, v_in, cap_in))
            
            # Verificar si se introdujo un ciclo
            hay_ciclo, ciclos = tiene_ciclos(numero_nodos, nuevas_aristas)
            if hay_ciclo:
                st.sidebar.error(f"❌ ¡Ciclo detectado! No se puede añadir esta arista. Ciclo: {ciclos[0]}")
            else:
                st.session_state.aristas = nuevas_aristas
                st.session_state.historial = []
                st.session_state.paso_actual = 0

    if st.sidebar.button("🗑️ Limpiar aristas"):
        st.session_state.aristas = []
        st.session_state.historial = []
        st.session_state.paso_actual = 0

# --- PANEL PRINCIPAL ---

# Verificación de ciclos preventiva
hay_ciclo, ciclos = tiene_ciclos(st.session_state.numero_nodos, st.session_state.aristas)
if hay_ciclo:
    st.error(f"⚠️ El grafo actual contiene ciclos: {ciclos}. Por favor, corrige la estructura.")

# Mapeo de Nodos
indices_nodos = list(range(st.session_state.numero_nodos))

st.subheader("1️⃣ Selección de Fuentes y Sumideros")
col_s, col_t = st.columns(2)

fuentes_seleccionadas = col_s.multiselect("Selecciona Fuentes Originales:", indices_nodos, default=[0] if indices_nodos else [])
sumideros_seleccionados = col_t.multiselect("Selecciona Sumideros Originales:", indices_nodos, default=[st.session_state.numero_nodos - 1] if indices_nodos else [])

# Ficticios para múltiples fuentes/sumideros
aristas_efectivas = list(st.session_state.aristas)
num_nodos_efectivos = st.session_state.numero_nodos
fuente_actual = fuentes_seleccionadas[0] if len(fuentes_seleccionadas) == 1 else None
sumidero_actual = sumideros_seleccionados[0] if len(sumideros_seleccionados) == 1 else None

nombres_visibles_nodos = {i: str(i) for i in range(st.session_state.numero_nodos)}

if len(fuentes_seleccionadas) > 1 or len(sumideros_seleccionados) > 1:
    st.info("ℹ️ Se incorporará un Origen Ficticio (S) y/o Destino Ficticio (T) con aristas de capacidad ∞.")
    
    id_fuente_ficticia = num_nodos_efectivos
    id_sumidero_ficticio = num_nodos_efectivos + (1 if len(fuentes_seleccionadas) > 1 else 0)
    
    if len(fuentes_seleccionadas) > 1:
        for nodo_s in fuentes_seleccionadas:
            aristas_efectivas.append((id_fuente_ficticia, nodo_s, 999999)) # Representa ∞
        fuente_actual = id_fuente_ficticia
        nombres_visibles_nodos[id_fuente_ficticia] = "S (Ficticia)"
        num_nodos_efectivos += 1

    if len(sumideros_seleccionados) > 1:
        for nodo_t in sumideros_seleccionados:
            aristas_efectivas.append((nodo_t, id_sumidero_ficticio, 999999)) # Representa ∞
        sumidero_actual = id_sumidero_ficticio
        nombres_visibles_nodos[id_sumidero_ficticio] = "T (Ficticio)"
        num_nodos_efectivos += 1

# Botón para iniciar / reiniciar la ejecución
st.subheader("2️⃣ Simulación del algoritmo de Ford Fulkerson")

if fuente_actual is None or sumidero_actual is None:
    st.warning("Debe haber al menos una fuente y un sumidero seleccionados.")
else:
    if st.button("🚀 Ejecutar / Reiniciar Simulación"):
        st.session_state.historial = ejecutar_ford_fulkerson_pasos(
            num_nodos_efectivos, aristas_efectivas, fuente_actual, sumidero_actual
        )
        st.session_state.paso_actual = 0

# --- NAVEGACIÓN PASO A PASO Y VISUALIZACIÓN ---
if st.session_state.historial:
    historial = st.session_state.historial
    paso_actual = st.session_state.paso_actual
    total_pasos = len(historial) - 1

    # Controles de avance
    c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
    if c1.button("⏮️ Inicio"):
        st.session_state.paso_actual = 0
    if c2.button("◀️ Anterior") and paso_actual > 0:
        st.session_state.paso_actual -= 1
    if c3.button("Siguiente ▶️") and paso_actual < total_pasos:
        st.session_state.paso_actual += 1
    if c4.button("⏭️ Final"):
        st.session_state.paso_actual = total_pasos

    paso_actual = st.session_state.paso_actual
    info_paso = historial[paso_actual]

    # Estado y mensajes
    st.markdown(f"**Paso {paso_actual} de {total_pasos}:** {info_paso['mensaje']}")
    st.metric(label="Flujo total actual", value=f"{info_paso['flujo_total']} unidades")

    # Renderizar Grafo
    html_grafo = renderizar_grafo_pyvis(
        num_nodos_efectivos, aristas_efectivas, info_paso, fuente_actual, sumidero_actual, nombres_visibles_nodos
    )
    componentes.html(html_grafo, height=540)

    # Detalle en el Paso Final
    if info_paso.get("finalizado", False):
        st.success("🎉 **RESULTADO FINAL Y CORTE MÍNIMO**")
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.markdown(f"**Valor del Flujo Máximo:** `{info_paso['flujo_total']}`")
            st.markdown(f"**Capacidad del Corte Mínimo c(S,T):** `{info_paso['capacidad_corte']}`")
            st.markdown("**Verificación:** \(\vert{}f\vert{} = c(S,T)\) (Teorema de Flujo Máximo y Corte Mínimo)")

        with col_res2:
            nombres_S = [nombres_visibles_nodos[i] for i in info_paso['conjunto_S']]
            nombres_T = [nombres_visibles_nodos[i] for i in info_paso['conjunto_T']]
            st.markdown(f"**Conjunto S (Fuente):** {nombres_S}")
            st.markdown(f"**Conjunto T (Sumidero):** {nombres_T}")

        st.subheader("📋 Asignación de flujo por arista")
        tabla_datos = []
        for u, v, c in aristas_efectivas:
            f = info_paso['flujo'].get((u, v), 0)
            cap_str = "∞" if c == 999999 else str(c)
            tabla_datos.append({
                "Origen": nombres_visibles_nodos[u],
                "Destino": nombres_visibles_nodos[v],
                "Flujo Asignado": f,
                "Capacidad": cap_str,
                "Saturada": "Sí" if f == c and c != 999999 else "No"
            })
        st.dataframe(tabla_datos, use_container_width=True)