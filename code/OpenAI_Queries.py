from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from urllib.error import URLError
import pandas as pd
from utilities import utils  # Eliminado translator ya que no se usará
import os

# Inicialización sin necesidad de DataFrame
utils.initialize(engine='gpt-35-turbo-instruct')  # CAMBIO 1

try:
    default_prompt = "" 
    default_question = "" 
    default_answer = ""

    if 'question' not in st.session_state:
        st.session_state['question'] = default_question
    if 'prompt' not in st.session_state:
        # Actualizado a español
        st.session_state['prompt'] = os.getenv("INDICACIÓN_DE_PREGUNTA", 
            "Por favor, responde a la pregunta utilizando únicamente la información presente en el texto anterior. "
            "Si no puedes encontrarla, responde 'No está en el texto'.\nPregunta: _QUESTION_\nRespuesta:").replace(r'\n', '\n')
    if 'response' not in st.session_state:
        st.session_state['response'] = {
            "choices" :[{
                "text" : default_answer
            }]
        }    
    if 'limit_response' not in st.session_state:
        st.session_state['limit_response'] = True
    if 'full_prompt' not in st.session_state:
        st.session_state['full_prompt'] = ""
    if 'source_file' not in st.session_state:
        st.session_state['source_file'] = ""
    
    # Configuración de página
    menu_items = {
        'Get help': None,
        'Report a bug': None,
        'About': '''
        ## Embeddings App
        Aplicación de prueba de embeddings.
        '''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.image(os.path.join('images','microsoft.png'))

    col1, col2, col3 = st.columns([2,2,2])
    with col3:
        with st.expander("Configuración"):
            # Modelos actualizados
            model_options = ["gpt-35-turbo-instruct", "gpt-3.5-turbo-instruct", "gpt-4"]
            model = st.selectbox(
                "Modelo OpenAI",
                options=model_options,
                index=0  # 'gpt-35-turbo-instruct' por defecto
            )
            st.text_area("Prompt", height=100, key='prompt')
            st.tokens_response = st.slider("Longitud de respuesta (tokens)", 100, 500, 400)
            st.temperature = st.slider("Temperatura (creatividad)", 0.0, 1.0, 0.1)

    question = st.text_input("Respuesta Semántica OpenAI", default_question)

    if question != '':
        if question != st.session_state['question']:
            st.session_state['question'] = question
            # CAMBIO PRINCIPAL: Nueva llamada a get_semantic_answer
            st.session_state['full_prompt'], st.session_state['response'], st.session_state['source_file'] = utils.get_semantic_answer(
                question=question, 
                explicit_prompt=st.session_state['prompt'],
                model=model, 
                tokens_response=st.tokens_response, 
                temperature=st.temperature
            )
            
            # Mostrar resultados
            st.write(f"P: {question}")  
            if st.session_state['response'] is not None:
                respuesta = st.session_state['response'].get('choices', [{}])[0].get('text', '')
                st.write(f"R: {respuesta}")
                
                with st.expander("Contexto de Pregunta y Respuesta"):
                    st.text(st.session_state['full_prompt'])
                
                if "No está en el texto" in respuesta or "No se encontraron" in respuesta:
                    st.session_state['source_file'] = ''
                else:
                    st.write(st.session_state['source_file'])
            else:
                st.error("No se recibió respuesta de OpenAI")
            
        else:
            # Mostrar resultados de la sesión actual
            st.write(f"P: {st.session_state['question']}")  
            if st.session_state['response'] is not None:
                respuesta = st.session_state['response'].get('choices', [{}])[0].get('text', '')
                st.write(f"R: {respuesta}")
                
                with st.expander("Contexto de Pregunta y Respuesta"):
                    st.text(st.session_state['full_prompt'])
                
                if "No está en el texto" in respuesta or "No se encontraron" in respuesta:
                    st.session_state['source_file'] = ''
                else:
                    st.write(st.session_state['source_file'])
            else:
                st.error("No se recibió respuesta de OpenAI")
        
except URLError as e:
    st.error(
        """
        **Esta demostración requiere acceso a internet.**
        Error de conexión: %s
        """
        % e.reason
    )