import streamlit as st
from urllib.error import URLError
import pandas as pd
import os, json, re, io
from os import path
import zipfile
from utilities import utils, redisembeddings
from utilities.formrecognizer import analyze_read
from utilities.azureblobstorage import upload_file, get_all_files, upsert_blob_metadata
import requests
import mimetypes

def calcular_embeddings():
    """
    Calcula y almacena embeddings para el texto en sesión
    """
    embeddings = utils.chunk_and_embed(st.session_state['texto_documento'])
    if embeddings:
        # Almacenar embeddings en Redis
        redisembeddings.set_document(embeddings)
        st.success("Embeddings calculados y almacenados correctamente")
        
        # Mostrar conteo de tokens
        token_len = utils.get_token_count(st.session_state['texto_documento'])
        if token_len >= 3000:
            st.warning(f'Tu texto tiene {token_len} tokens. Para una representación completa, considera reducirlo a menos de 3000 tokens')
    else:
        st.error("Error al calcular embeddings")

def procesar_archivos_remotos():
    """
    Inicia el procesamiento remoto de archivos para conversión y embeddings
    """
    response = requests.post(os.getenv('CONVERT_ADD_EMBEDDINGS_URL'))
    if response.status_code == 200:
        st.success(f"{response.text}\nNota: Este proceso es asincrónico y puede tardar varios minutos en completarse.")
    else:
        st.error(f"Error al iniciar el proceso: {response.text}")

def eliminar_documento():
    """
    Elimina un documento de la base de conocimientos
    """
    if 'documento_a_eliminar' in st.session_state:
        redisembeddings.delete_document(st.session_state['documento_a_eliminar'])
        st.success("Documento eliminado correctamente")

try:
    # Configurar página
    menu_items = {
        'Obtener ayuda': None,
        'Reportar error': None,
        'Acerca de': '''
        ## Aplicación de Embeddings
        Sistema de gestión de conocimientos con embeddings semánticos.
        '''
    }
    st.set_page_config(
        layout="wide", 
        menu_items=menu_items,
        page_title="Gestor de Conocimiento",
        page_icon="🧠"
    )

    # Sección 1: Añadir documento individual
    with st.expander("Añadir un documento a la base de conocimientos", expanded=True):
        st.info("Para documentos PDF grandes, usa la opción 'Añadir documentos en lote' más abajo.")
        
        archivo_subido = st.file_uploader(
            "Sube un documento para añadirlo a la base de conocimientos", 
            type=['pdf','jpeg','jpg','png', 'txt', 'docx', 'pptx']
        )
        
        if archivo_subido is not None:
            # Leer contenido del archivo
            bytes_data = archivo_subido.getvalue()
            nombre_archivo = archivo_subido.name

            if st.session_state.get('nombre_archivo', '') != nombre_archivo:
                # Subir nuevo archivo
                st.session_state['nombre_archivo'] = nombre_archivo
                tipo_contenido = mimetypes.MimeTypes().guess_type(nombre_archivo)[0]
                url_archivo = upload_file(bytes_data, nombre_archivo, content_type=tipo_contenido)

                if nombre_archivo.endswith('.txt'):
                    # Procesar directamente archivos de texto
                    utils.add_embeddings(
                        archivo_subido.read().decode('utf-8'), 
                        nombre_archivo
                    )
                    st.success(f"Documento {nombre_archivo} añadido a la base de conocimientos.")
                else:
                    # Procesar otros tipos de archivos
                    if utils.convert_file_and_add_embeddings(url_archivo, nombre_archivo):
                        st.success(f"Documento {nombre_archivo} procesado y añadido a la base de conocimientos.")
                    else:
                        st.error(f"Error al procesar el documento {nombre_archivo}")

    # Sección 2: Añadir texto directo
    with st.expander("Añadir texto a la base de conocimientos", expanded=False):
        col1, col2 = st.columns([3,1])
        with col1: 
            st.text_area("Introduce texto y haz clic en 'Calcular Embeddings'", 
                         height=300, key='texto_documento')
        
        with col2:
            st.button("Calcular Embeddings", on_click=calcular_embeddings, 
                      help="Genera embeddings semánticos para el texto introducido")
            
            # Mostrar modelo de embeddings
            modelo_embeddings = utils.get_embeddings_model()['doc']
            st.info(f"Modelo de embeddings: {modelo_embeddings}")

    # Sección 3: Procesamiento por lotes
    with st.expander("Añadir documentos en Lote", expanded=False):
        archivos_subidos = st.file_uploader(
            "Sube múltiples documentos para añadirlos al almacenamiento", 
            type=['pdf','jpeg','jpg','png', 'txt', 'docx', 'pptx'], 
            accept_multiple_files=True
        )
        
        if archivos_subidos:
            for archivo in archivos_subidos:
                bytes_data = archivo.getvalue()
                nombre_archivo = archivo.name
                tipo_contenido = mimetypes.MimeTypes().guess_type(nombre_archivo)[0]
                upload_file(bytes_data, nombre_archivo, content_type=tipo_contenido)
                st.success(f"Archivo {nombre_archivo} subido correctamente")
        
        st.button("Procesar todos los archivos", on_click=procesar_archivos_remotos,
                  help="Inicia el procesamiento asincrónico de todos los archivos subidos")

    # Sección 4: Gestión de documentos
    with st.expander("Documentos en la Base de Conocimientos", expanded=False):
        # Obtener documentos de Redis
        documentos = redisembeddings.get_documents()
        
        if len(documentos) == 0:
            st.info("No se encontraron documentos. Añade contenido usando las opciones superiores.")
        else:
            # Mostrar tabla con documentos
            df = pd.DataFrame(documentos)
            st.dataframe(df[['filename', 'text']].head(1000), height=400)
            
            # Opción para eliminar documentos
            documentos_lista = [doc['filename'] for doc in documentos]
            seleccionado = st.selectbox("Seleccionar documento para eliminar", documentos_lista, key='documento_a_eliminar')
            st.button("Eliminar documento seleccionado", on_click=eliminar_documento, 
                      help="Elimina permanentemente el documento de la base de conocimientos")

except URLError as e:
    st.error(
        f"""
        **Esta aplicación requiere acceso a internet.**
        Error de conexión: {e.reason}
        """
    )
except Exception as e:
    st.error(f"Error inesperado: {str(e)}")