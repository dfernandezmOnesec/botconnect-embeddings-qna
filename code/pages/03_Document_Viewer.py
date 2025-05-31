import streamlit as st
from urllib.error import URLError
import pandas as pd
from utilities.azureblobstorage import get_all_files
from utilities import utils
import os

########## INICIO - PRINCIPAL ##########
try:
    # Configurar página
    menu_items = {
        'Obtener ayuda': None,
        'Reportar error': None,
        'Acerca de': '''
        ## Gestor de Documentos
        
        Sistema de gestión y análisis de documentos con embeddings semánticos.
        '''
    }
    
    st.set_page_config(
        layout="wide", 
        menu_items=menu_items,
        page_title="Gestor de Documentos",
        page_icon="📄"
    )

    # Estilo para ocultar elementos de Streamlit
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Título y descripción
    st.title("Gestor de Documentos")
    st.markdown("""
    **Visualiza y gestiona todos los documentos almacenados en tu repositorio de conocimiento.**
    Cada documento ha sido procesado para extraer su contenido y generar embeddings semánticos.
    """)
    
    # Verificar conexión con OpenAI
    if not utils.initialize():
        st.error("Error de conexión con el servicio de embeddings. Verifica la configuración.")
        st.stop()

    # Obtener y mostrar documentos
    st.subheader("Documentos en el repositorio")
    with st.spinner("Cargando documentos..."):
        documentos = get_all_files()
        
        if documentos.empty:
            st.info("No se encontraron documentos. Sube archivos usando la opción 'Añadir Documentos'.")
            st.stop()
        
        # Procesar metadatos
        documentos['tamaño'] = documentos['size'].apply(lambda x: f"{x/1024:.1f} KB")
        documentos['subido'] = pd.to_datetime(documentos['creation_time']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Mostrar tabla con documentos
        columnas = ['name', 'tamaño', 'subido', 'converted', 'embeddings_added']
        documentos_mostrar = documentos[columnas].rename(columns={
            'name': 'Nombre',
            'tamaño': 'Tamaño',
            'subido': 'Fecha de Subida',
            'converted': 'Convertido',
            'embeddings_added': 'Embeddings'
        })
        
        st.dataframe(
            documentos_mostrar,
            use_container_width=True,
            height=600
        )
        
        # Estadísticas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Documentos", len(documentos))
        col2.metric("Documentos Procesados", documentos['converted'].sum())
        col3.metric("Con Embeddings", documentos['embeddings_added'].sum())
        
        # Filtros de búsqueda
        with st.expander("Buscar Documentos", expanded=False):
            termino = st.text_input("Buscar por nombre:")
            if termino:
                filtrados = documentos[documentos['name'].str.contains(termino, case=False)]
                st.dataframe(filtrados[columnas].rename(columns={
                    'name': 'Nombre',
                    'tamaño': 'Tamaño',
                    'subido': 'Fecha de Subida',
                    'converted': 'Convertido',
                    'embeddings_added': 'Embeddings'
                }))
        
        # Descargar lista completa
        csv = documentos[columnas].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar lista completa (CSV)",
            data=csv,
            file_name="documentos.csv",
            mime="text/csv"
        )

except URLError as e:
    st.error(
        f"""
        **Esta aplicación requiere acceso a internet.**
        
        Error de conexión: {e.reason}
        """
    )
except Exception as e:
    st.error(f"Error inesperado: {str(e)}")

########## FIN - PRINCIPAL ##########