import streamlit as st
from urllib.error import URLError
import pandas as pd
from utilities import redisembeddings
import os

def eliminar_documento():
    """
    Elimina un documento de la base de conocimientos usando su ID
    """
    if 'documento_a_eliminar' in st.session_state:
        id_documento = st.session_state['documento_a_eliminar']
        if redisembeddings.delete_document(id_documento):
            st.success(f"Documento con ID {id_documento} eliminado correctamente")
            # Actualizar los datos mostrados
            st.session_state.documentos = obtener_documentos()
            st.experimental_rerun()
        else:
            st.error(f"Error al eliminar el documento con ID {id_documento}")

def obtener_documentos():
    """
    Obtiene todos los documentos de Redis y los convierte en DataFrame
    """
    documentos = redisembeddings.get_documents()
    if documentos:
        return pd.DataFrame(documentos)
    return pd.DataFrame()

try:
    # Configurar página
    menu_items = {
        'Obtener ayuda': None,
        'Reportar error': None,
        'Acerca de': '''
        ## Gestor de Conocimiento
        
        Sistema de gestión de embeddings para búsquedas semánticas.
        '''
    }
    
    st.set_page_config(
        layout="wide", 
        menu_items=menu_items,
        page_title="Gestor de Embeddings",
        page_icon="🧠"
    )
    
    # Título y descripción
    st.title("Gestión de Embeddings")
    st.markdown("""
    **Visualiza y gestiona todos los embeddings almacenados en tu base de conocimiento.**
    Cada entrada representa un fragmento de texto con su representación vectorial asociada.
    """)
    
    # Obtener documentos (con caché para mejorar rendimiento)
    if 'documentos' not in st.session_state:
        with st.spinner("Cargando embeddings..."):
            st.session_state.documentos = obtener_documentos()
    
    documentos = st.session_state.documentos
    
    # Mostrar mensaje si no hay documentos
    if documentos.empty:
        st.warning("No se encontraron embeddings. Dirígete a la pestaña 'Añadir Documentos' para agregar contenido.")
        st.stop()
    
    # Mostrar tabla de documentos
    st.subheader("Documentos en la Base de Conocimiento")
    st.dataframe(documentos, height=600, use_container_width=True)
    
    # Estadísticas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Documentos", len(documentos))
    col2.metric("Campos por Documento", len(documentos.columns) if not documentos.empty else 0)
    
    # Sección de gestión
    with st.expander("Gestión de Documentos", expanded=True):
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Descargar datos como CSV
            st.download_button(
                label="Descargar CSV",
                data=documentos.to_csv(index=False, encoding='utf-8'),
                file_name="embeddings.csv",
                mime="text/csv",
                help="Descarga todos los embeddings en formato CSV"
            )
        
        with col2:
            # Seleccionar documento para eliminar
            if not documentos.empty and 'id' in documentos.columns:
                opciones = documentos['id'].tolist()
                st.selectbox(
                    "Selecciona un ID de documento para eliminar",
                    options=opciones,
                    key='documento_a_eliminar',
                    help="Selecciona el documento que deseas eliminar permanentemente"
                )
        
        with col3:
            st.text("")  # Espaciador
            st.text("")  # Espaciador
            # Botón para eliminar
            st.button(
                "Eliminar Documento", 
                on_click=eliminar_documento,
                type="primary",
                help="Elimina permanentemente el documento seleccionado"
            )
    
    # Información adicional
    st.info("""
    **Notas:**
    - Cada documento representa un fragmento de texto procesado
    - Los embeddings se almacenan como vectores numéricos
    - La eliminación de documentos es permanente
    """)

except URLError as e:
    st.error(
        f"""
        **Esta aplicación requiere acceso a internet.**
        
        Error de conexión: {e.reason}
        """
    )
except Exception as e:
    st.error(f"Error inesperado: {str(e)}")