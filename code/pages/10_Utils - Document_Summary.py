import streamlit as st
from utilities import utils
import os

# Configuración de la página
st.set_page_config(
    page_title="Resumen de Documentos",
    page_icon="📝",
    layout="centered",
    menu_items={
        'Obtener ayuda': None,
        'Reportar error': None,
        'Acerca de': '''
        ## Herramienta de Resumen de Texto
        Genera resúmenes automáticos usando modelos avanzados de IA
        '''
    }
)

# Estilos personalizados
st.markdown("""
<style>
    .stApp {
        max-width: 900px;
        margin: 0 auto;
    }
    .header {
        text-align: center;
        padding: 20px 0;
        border-bottom: 2px solid #4b6cb7;
        margin-bottom: 30px;
    }
    .result-card {
        background-color: #f0f4ff;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .prompt-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        font-family: monospace;
        font-size: 14px;
        margin: 10px 0;
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
    .clear-btn {
        background-color: #f8f9fa !important;
        color: #333 !important;
        border: 1px solid #ddd !important;
    }
</style>
""", unsafe_allow_html=True)

def generar_resumen():
    """Genera el resumen usando el modelo de IA"""
    with st.spinner("Generando resumen..."):
        try:
            # Obtener modelo configurado
            model = os.getenv('OPENAI_ENGINES', 'gpt-3.5-turbo-instruct')
            
            # Generar respuesta
            _, response = utils.get_completion(
                prompt=obtener_prompt(),
                max_tokens=500,
                model=model
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                st.session_state['resumen'] = response['choices'][0]['text'].encode().decode()
            else:
                st.session_state['resumen'] = "❌ Error: No se recibió respuesta válida"
                
        except Exception as e:
            st.session_state['resumen'] = f"❌ Error: {str(e)}"

def limpiar_resumen():
    """Borra el resumen de la sesión actual"""
    st.session_state.pop('resumen', None)

def obtener_prompt():
    """Genera el prompt basado en el texto y tipo de resumen"""
    texto = st.session_state.get('texto', '')
    tipo_resumen = st.session_state.get('tipo_resumen', 'Resumen básico')
    
    if not texto:
        return "Por favor ingresa algún texto para resumir"
    
    # Plantillas de prompts en español
    prompts = {
        "Resumen básico": f"Resume el siguiente texto de manera concisa:\n\n{texto}\n\nResumen:",
        "Puntos clave": f"Extrae los puntos clave del siguiente texto en formato de lista con viñetas:\n\n{texto}\n\nPuntos clave:",
        "Explicación sencilla": f"Explica el siguiente texto de manera simple, como si se lo estuvieras contando a un estudiante de secundaria:\n\n{texto}\n\nExplicación:",
        "Resumen ejecutivo": f"Crea un resumen ejecutivo (máximo 100 palabras) del siguiente texto:\n\n{texto}\n\nResumen ejecutivo:",
        "Análisis crítico": f"Realiza un análisis crítico del siguiente texto, destacando fortalezas y debilidades:\n\n{texto}\n\nAnálisis:"
    }
    
    return prompts.get(tipo_resumen, prompts["Resumen básico"])

# Título de la aplicación
st.markdown('<div class="header"><h1>📝 Resumen de Documentos</h1><p>Genera resúmenes automáticos usando IA</p></div>', unsafe_allow_html=True)

# Selector de tipo de resumen
tipos_resumen = [
    "Resumen básico",
    "Puntos clave",
    "Explicación sencilla",
    "Resumen ejecutivo",
    "Análisis crítico"
]

st.selectbox(
    "Selecciona el tipo de resumen:",
    options=tipos_resumen,
    index=0,
    key='tipo_resumen',
    help="Elige cómo quieres que se genere el resumen"
)

# Área de texto para entrada
st.text_area(
    "Texto a resumir:",
    height=250,
    key='texto',
    placeholder="Pega aquí el texto que deseas resumir...",
    help="Ingresa cualquier texto que desees resumir o analizar"
)

# Botones de acción
col1, col2 = st.columns(2)
with col1:
    st.button(
        "✨ Generar Resumen", 
        on_click=generar_resumen,
        use_container_width=True
    )
with col2:
    st.button(
        "🧹 Limpiar Resultado", 
        on_click=limpiar_resumen,
        use_container_width=True,
        type="secondary"
    )

# Mostrar resultado
if 'resumen' in st.session_state:
    st.markdown("### Resultado del Resumen")
    st.markdown(f'<div class="result-card">{st.session_state["resumen"]}</div>', unsafe_allow_html=True)

# Mostrar el prompt utilizado
st.markdown("### Prompt Utilizado")
st.markdown(f'<div class="prompt-card">{obtener_prompt()}</div>', unsafe_allow_html=True)

# Sección de información adicional
with st.expander("💡 Consejos para mejores resultados"):
    st.markdown("""
    - **Textos largos**: Para documentos extensos (>1000 palabras), considera dividirlos en secciones
    - **Especificidad**: Cuanto más específico sea tu texto, mejor será el resumen
    - **Idioma**: La herramienta funciona mejor con textos en español
    - **Personalización**: Si necesitas un formato específico, menciónalo en el texto
    - **Verificación**: Siempre revisa los resultados, especialmente para contenido crítico
    """)

# Nota sobre modelos
st.info("""
**Nota:** Esta herramienta utiliza modelos de lenguaje avanzados de OpenAI. 
El modelo actual es `gpt-3.5-turbo-instruct` (puede configurarse en variables de entorno).
""")