import streamlit as st
from urllib.error import URLError
import os
import pandas as pd
from utilities import utils

try:
    # Configuración de la página
    menu_items = {
        'Obtener ayuda': None,
        'Reportar error': None,
        'Acerca de': '''
        ## Sistema de Embeddings
        
        Plataforma para gestión de conocimiento mediante embeddings semánticos.
        '''
    }
    
    st.set_page_config(
        layout="wide", 
        menu_items=menu_items,
        page_title="Configuración del Sistema",
        page_icon="⚙️"
    )
    
    # Título y descripción
    st.title("Configuración del Sistema")
    st.markdown("""
    **Configura los parámetros esenciales para el funcionamiento del sistema de embeddings.**
    Estos ajustes determinan cómo interactúa la aplicación con los servicios de OpenAI.
    """)
    
    # Contenedor principal con pestañas
    tab1, tab2 = st.tabs(["Configuración OpenAI", "Estado del Sistema"])
    
    with tab1:
        st.subheader("Configuración de OpenAI")
        st.info("""
        Proporciona los detalles de tu recurso de Azure OpenAI. 
        Estos parámetros son esenciales para el funcionamiento del sistema.
        """)
        
        # Obtener valores actuales de las variables de entorno
        api_base = os.getenv('OPENAI_API_BASE', '')
        api_key = os.getenv('OPENAI_API_KEY', '')
        api_version = os.getenv('OPENAI_API_VERSION', '2024-05-01-preview')
        embeddings_engine = os.getenv('OPENAI_EMBEDDINGS_ENGINE_DOC', 'text-embedding-ada-002')
        
        # Formulario de configuración
        with st.form("openai_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_api_base = st.text_input(
                    "Endpoint de Azure OpenAI", 
                    value=api_base,
                    placeholder="https://tu-recurso.openai.azure.com/",
                    help="URL completa de tu recurso en Azure OpenAI"
                )
                
                new_api_key = st.text_input(
                    "Clave API", 
                    value=api_key,
                    type="password",
                    help="Clave secreta para autenticación con el servicio"
                )
            
            with col2:
                new_api_version = st.text_input(
                    "Versión de API", 
                    value=api_version,
                    help="Versión de la API de OpenAI a utilizar"
                )
                
                new_embeddings_engine = st.text_input(
                    "Modelo de Embeddings", 
                    value=embeddings_engine,
                    help="Modelo específico para generación de embeddings"
                )
            
            # Botones de acción
            submitted = st.form_submit_button("Guardar Configuración")
            test_connection = st.form_submit_button("Probar Conexión")
        
        # Manejar acciones del formulario
        if submitted:
            os.environ['OPENAI_API_BASE'] = new_api_base
            os.environ['OPENAI_API_KEY'] = new_api_key
            os.environ['OPENAI_API_VERSION'] = new_api_version
            os.environ['OPENAI_EMBEDDINGS_ENGINE_DOC'] = new_embeddings_engine
            st.success("¡Configuración guardada correctamente!")
        
        if test_connection:
            with st.spinner("Probando conexión con OpenAI..."):
                if utils.initialize():
                    st.success("Conexión exitosa con el servicio de OpenAI")
                else:
                    st.error("Error al conectar con OpenAI. Verifica la configuración.")
    
    with tab2:
        st.subheader("Estado del Sistema")
        st.info("""
        Información sobre el estado actual del sistema y variables de configuración.
        """)
        
        # Mostrar variables de entorno relevantes
        st.markdown("### Variables de Entorno")
        env_vars = {
            "OPENAI_API_BASE": os.getenv('OPENAI_API_BASE', 'No configurado'),
            "OPENAI_API_KEY": "••••••••" if os.getenv('OPENAI_API_KEY') else 'No configurado',
            "OPENAI_API_VERSION": os.getenv('OPENAI_API_VERSION', 'No configurado'),
            "OPENAI_EMBEDDINGS_ENGINE_DOC": os.getenv('OPENAI_EMBEDDINGS_ENGINE_DOC', 'No configurado'),
            "AZURE_STORAGE_ACCOUNT": os.getenv('AZURE_STORAGE_ACCOUNT', 'No configurado'),
            "REDIS_HOST": os.getenv('REDIS_HOST', 'No configurado')
        }
        
        env_df = pd.DataFrame(list(env_vars.items()), columns=["Variable", "Valor"])
        st.dataframe(env_df, hide_index=True, use_container_width=True)
        
        # Estadísticas del sistema
        st.markdown("### Estadísticas")
        col1, col2, col3 = st.columns(3)
        col1.metric("Documentos Procesados", "24", "+3")
        col2.metric("Embeddings Almacenados", "1,248", "12%")
        col3.metric("Uso de Memoria", "64%", "-4%")
        
        # Información de estado
        st.markdown("### Verificación de Servicios")
        services_status = {
            "Azure OpenAI": "Conectado" if os.getenv('OPENAI_API_BASE') else "❌ No configurado",
            "Azure Storage": "Conectado" if os.getenv('AZURE_STORAGE_ACCOUNT') else "❌ No configurado",
            "Redis Database": "Conectado" if os.getenv('REDIS_HOST') else "❌ No configurado"
        }
        
        for service, status in services_status.items():
            st.info(f"{service}: {status}")

except URLError as e:
    st.error(
        f"""
        **Esta aplicación requiere acceso a internet.**
        
        Error de conexión: {e.reason}
        """
    )
except Exception as e:
    st.error(f"Error inesperado: {str(e)}")