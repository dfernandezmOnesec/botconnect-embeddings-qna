import streamlit as st
import pandas as pd
from utilities import utils, redisembeddings
import os
import json

# Configuración de la página
st.set_page_config(
    page_title="Explorador de Prompts - Comunidad Religiosa",
    page_icon="⛪",
    layout="wide",
    menu_items={
        'Obtener ayuda': None,
        'Reportar error': None,
        'Acerca de': '''
        ## Explorador de Prompts
        Herramienta para experimentar con prompts en documentos religiosos
        '''
    }
)

# Estilos personalizados
st.markdown("""
<style>
    .header {
        background-color: #4b6cb7;
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .card {
        background-color: #f0f4ff;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stButton>button {
        background-color: #4b6cb7;
        color: white;
        border-radius: 8px;
        padding: 8px 20px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #3a56a8;
        transform: translateY(-2px);
    }
    .prompt-example {
        background-color: #e0e7ff;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
    }
    .tag {
        display: inline-block;
        background-color: #e0e7ff;
        color: #4b6cb7;
        border-radius: 15px;
        padding: 3px 10px;
        margin: 2px;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

def limpiar_resultados():
    """Borra los resultados de la sesión actual"""
    st.session_state.pop('resultado', None)
    st.session_state.pop('resultados_procesados', None)

def ejecutar_prompt():
    """Ejecuta el prompt en el documento actual"""
    with st.spinner("Procesando documento..."):
        try:
            # Obtener modelo configurado
            modelo = os.getenv('OPENAI_ENGINES', 'gpt-3.5-turbo-instruct')
            
            # Generar respuesta
            _, respuesta = utils.get_completion(
                prompt=obtener_prompt(),
                max_tokens=1000,
                model=modelo
            )
            
            if respuesta and 'choices' in respuesta and len(respuesta['choices']) > 0:
                st.session_state['resultado'] = respuesta['choices'][0]['text'].encode().decode()
            else:
                st.session_state['resultado'] = "❌ Error: No se recibió respuesta válida"
                
        except Exception as e:
            st.session_state['resultado'] = f"❌ Error: {str(e)}"

def procesar_todos():
    """Procesa todos los documentos seleccionados"""
    if 'documentos' not in st.session_state or st.session_state['documentos'].empty:
        st.error("No hay documentos disponibles para procesar")
        return
        
    if not st.session_state['prompt']:
        st.error("Por favor ingresa un prompt primero")
        return
        
    with st.spinner(f"Procesando {len(st.session_state['documentos_seleccionados'])} documentos..."):
        try:
            resultados = []
            modelo = os.getenv('OPENAI_ENGINES', 'gpt-3.5-turbo-instruct')
            
            for _, doc in st.session_state['documentos'].iterrows():
                if doc['filename'] in st.session_state['documentos_seleccionados']:
                    prompt_completo = f"{doc['text']}\n{st.session_state['prompt']}"
                    
                    # Ejecutar prompt
                    _, respuesta = utils.get_completion(
                        prompt=prompt_completo,
                        max_tokens=1000,
                        model=modelo
                    )
                    
                    if respuesta and 'choices' in respuesta and len(respuesta['choices']) > 0:
                        resultado = respuesta['choices'][0]['text'].encode().decode()
                        resultados.append({
                            'id_documento': doc['id'],
                            'nombre_documento': doc['filename'],
                            'resultado': resultado
                        })
            
            # Guardar resultados en sesión
            st.session_state['resultados_procesados'] = pd.DataFrame(resultados)
            st.success(f"Procesados {len(resultados)} documentos con éxito")
            
        except Exception as e:
            st.error(f"Error al procesar documentos: {str(e)}")

def obtener_prompt():
    """Combina el texto del documento con el prompt personalizado"""
    return f"{st.session_state['texto_documento']}\n{st.session_state['prompt']}"

def cargar_ejemplo_prompt(ejemplo):
    """Carga un ejemplo de prompt en el área de texto"""
    st.session_state['prompt'] = ejemplo

# Título de la aplicación
st.markdown('<div class="header"><h1>⛪ Explorador de Prompts para Comunidades Religiosas</h1></div>', unsafe_allow_html=True)

# Obtener documentos de Redis
if 'documentos' not in st.session_state:
    documentos = redisembeddings.get_documents()
    st.session_state['documentos'] = documentos
else:
    documentos = st.session_state['documentos']

# Mostrar advertencia si no hay documentos
if documentos.empty:
    st.warning("No se encontraron documentos. Por favor agrega documentos en la pestaña correspondiente.")
    st.stop()

# Columnas principales
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Documentos Disponibles")
    
    # Filtrar nombres base de documentos
    nombres_base = sorted(set([doc.partition('_chunk_')[0] for doc in documentos['filename']]))
    
    # Seleccionar documentos
    documentos_seleccionados = st.multiselect(
        "Seleccionar documentos para procesar:",
        options=nombres_base,
        key='documentos_seleccionados',
        help="Selecciona los documentos que deseas procesar"
    )
    
    # Mostrar documentos filtrados
    st.markdown("**Fragmentos disponibles:**")
    if documentos_seleccionados:
        fragmentos = documentos[documentos['filename'].str.startswith(tuple(documentos_seleccionados))]
        for _, frag in fragmentos.iterrows():
            st.markdown(f"📄 **{frag['filename']}**")
            with st.expander("Ver fragmento"):
                st.text(frag['text'][:500] + "..." if len(frag['text']) > 500 else frag['text'])
    else:
        st.info("Selecciona documentos para ver sus fragmentos")

with col2:
    st.subheader("Configuración del Prompt")
    
    # Ejemplos de prompts para comunidades religiosas
    st.markdown("**Ejemplos de Prompts:**")
    ejemplos = {
        "Extraer eventos": "Extrae todos los eventos mencionados en el texto con sus fechas, lugares y descripciones.",
        "Identificar necesidades": "¿Qué necesidades o solicitudes de ayuda se mencionan en el texto?",
        "Resumir donaciones": "Resume la información sobre donaciones, incluyendo montos, propósitos y métodos de pago.",
        "Detectar contactos": "Identifica todas las personas mencionadas con sus roles e información de contacto.",
        "Analizar testimonios": "Extrae los testimonios personales o experiencias espirituales mencionadas."
    }
    
    for nombre, ejemplo in ejemplos.items():
        st.markdown(f'<div class="prompt-example" onclick="cargarEjemplo(\'{ejemplo}\')">{nombre}: {ejemplo}</div>', unsafe_allow_html=True)
    
    # Área para el prompt personalizado
    st.text_area(
        "Escribe tu prompt aquí:",
        height=150,
        key='prompt',
        help="Ingresa la instrucción que deseas aplicar a los documentos"
    )
    
    # Área para texto adicional
    st.text_area(
        "Texto adicional (opcional):",
        height=200,
        key='texto_documento',
        help="Puedes agregar texto adicional para combinar con los documentos"
    )
    
    # Botones de acción
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        st.button("▶️ Probar en texto", on_click=ejecutar_prompt, help="Ejecuta el prompt en el texto adicional")
    with col_btn2:
        st.button("🔁 Procesar selección", on_click=procesar_todos, help="Aplica el prompt a todos los documentos seleccionados")
    with col_btn3:
        st.button("🧹 Limpiar", on_click=limpiar_resultados, help="Borra todos los resultados")

# Sección de resultados
st.subheader("Resultados")

# Resultado de prueba en texto
if 'resultado' in st.session_state:
    st.markdown("**Resultado del texto adicional:**")
    st.markdown(f'<div class="card">{st.session_state["resultado"]}</div>', unsafe_allow_html=True)

# Resultados de documentos procesados
if 'resultados_procesados' in st.session_state and not st.session_state['resultados_procesados'].empty:
    st.markdown("**Resultados de documentos procesados:**")
    
    # Mostrar como tabla
    st.dataframe(st.session_state['resultados_procesados'], height=300)
    
    # Botón de descarga
    csv = st.session_state['resultados_procesados'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar resultados (CSV)",
        data=csv,
        file_name="resultados_prompts.csv",
        mime="text/csv"
    )
    
    # Mostrar detalles
    with st.expander("Ver detalles de resultados"):
        for _, fila in st.session_state['resultados_procesados'].iterrows():
            st.markdown(f"**Documento:** {fila['nombre_documento']}")
            st.markdown(f'<div class="card">{fila["resultado"]}</div>', unsafe_allow_html=True)
            st.divider()

# JavaScript para cargar ejemplos
st.markdown("""
<script>
function cargarEjemplo(texto) {
    parent.document.querySelector('textarea[aria-label="Escribe tu prompt aquí:"]').value = texto;
}
</script>
""", unsafe_allow_html=True)