# Contexto y Arquitectura
Eres un desarrollador experto en Python, especializado en interfaces con `Streamlit` y sistemas Multi-Agente con `LangGraph`. 

Mi proyecto es un Simplificador de Textos Médicos (Medical Plain Language Simplifier) basado en una arquitectura "Mixture of Agents" (MoA). El flujo de LangGraph incluye los siguientes agentes/nodos: `parallel_drafters`, `judge`, `fact_checker`, `readability_evaluator`, `editor` y `term_explainer`.

El estado final del grafo (`GraphState`) contiene, entre otras, estas variables clave:
- `complex_text` (str): El texto médico original.
- `current_simplified_text` (str): El texto simplificado final.
- `term_explanations` (Dict[str, Dict[str, str]]): Diccionario con los términos complejos detectados. Estructura: `{"término_en_texto": {"dictionary_term": "...", "explanation": "..."}}`.

# Requisitos de la Interfaz Web (Streamlit)

Tu tarea es crear el archivo `app.py` utilizando `streamlit` y `asyncio` para ejecutar el grafo de LangGraph. La UI debe tener exactamente la siguiente estructura:

## 1. Diseño Principal (Arriba)
- Un título principal y una breve descripción de la herramienta.
- Un formulario o área superior con un `st.text_area` para que el usuario introduzca el texto médico complejo y un botón "Simplificar".
- Una vez pulsado el botón, se deben mostrar **dos columnas principales (`st.columns(2)`)**:
  - **Columna Izquierda (Original):** Muestra el texto complejo introducido.
  - **Columna Derecha (Simplificado + Tooltips):** Mostrará el `current_simplified_text` final. 
  - **CRÍTICO - Interactividad (Tooltips):** En la columna derecha, debes implementar lógica de reemplazo de texto (Regex o `str.replace`) para buscar las claves de `term_explanations` dentro de `current_simplified_text`. Debes envolver estas palabras en HTML personalizado usando `<span class="tooltip">...</span>` y añadir CSS inyectado (`st.markdown("""<style>...</style>""", unsafe_allow_html=True)`) para que al pasar el ratón por encima del término subrayado, se muestre un cuadro flotante con el valor de la clave `explanation`.

## 2. Sección "Under the Hood" (Abajo)
- Debajo de las dos columnas, debe haber un expansor (`st.expander("Ver proceso de razonamiento de los agentes", expanded=True)`) o un contenedor similar.
- Dentro de este contenedor, debes mostrar **en directo** el progreso de la ejecución de LangGraph. 
- Utiliza la API de streaming de LangGraph (ej: `app.astream(initial_state, stream_mode="updates")`) para capturar cuándo cada nodo termina su ejecución.
- Por cada actualización de nodo capturada, muestra un bloque visual en Streamlit (puedes usar `st.info`, `st.success`, `st.chat_message` o simplemente `st.markdown`) indicando:
  - **El nombre del Agente/Nodo** que acaba de actuar (ej: 🧑‍⚖️ Juez, 🕵️‍♂️ Fact-Checker, 📝 Editor).
  - **La información relevante modificada** (ej: Si es el `judge`, mostrar qué estilo eligió; si es el `editor`, mostrar qué corrigió; si son los auditores, mostrar los booleanos de aprobación).
  - Usa `st.empty()` o contenedores dinámicos para que la interfaz se vaya rellenando en tiempo real mientras el grafo se ejecuta en *backend*, dando al usuario una sensación de "pensamiento en directo".

# Restricciones
- Debes importar el grafo compilado desde el archivo principal de mi proyecto (asume que se llama `src.workflow.build_graph()`).
- La interfaz debe estar por completo en inglés.
- Escribe código modular, limpio y comentado en inglés.
- Asegúrate de que el CSS de los tooltips no rompa el diseño general de Streamlit y soporte el modo claro/oscuro.