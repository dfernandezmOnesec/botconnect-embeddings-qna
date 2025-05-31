from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from urllib.error import URLError
import pandas as pd
from utilities import utils, translator
import os

# Actualización de modelo a 'gpt-35-turbo-instruct' 
df = utils.initialize(engine='gpt-35-turbo-instruct')  # CAMBIO 1

@st.cache_data(suppress_st_warning=True)  # CAMBIO 2: Usar st.cache_data en lugar de st.cache
def get_languages():
    return translator.get_available_languages()

try:

    default_prompt = "" 
    default_question = "" 
    default_answer = ""

    if 'question' not in st.session_state:
        st.session_state['question'] = default_question
    if 'prompt' not in st.session_state:
        st.session_state['prompt'] = os.getenv("INDICACIÓN_DE_PREGUNTA", "Por favor, responde a la pregunta utilizando únicamente la información presente en el texto anterior. Si no puedes encontrarla, responde 'No está en el texto'.\nPregunta: PREGUNTA\nRespuesta:").replace(r'\n', '\n')
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
    # Set page layout to wide screen and menu item
    menu_items = {
	'Get help': None,
	'Report a bug': None,
	'About': '''
	 ## Embeddings App
	 Embedding testing application.
	'''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    # Get available languages for translation
    available_languages = get_languages()

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.image(os.path.join('images','microsoft.png'))

    col1, col2, col3 = st.columns([2,2,2])
    with col3:
        with st.expander("Settings"):
            # CAMBIO 3: Actualizar modelos disponibles
            model_options = ["gpt-35-turbo-instruct", "gpt-3.5-turbo-instruct", "gpt-4"]
            model = st.selectbox(
                "OpenAI Model",
                options=model_options,
                index=0  # Seleccionar 'gpt-35-turbo-instruct' por defecto
            )
            st.text_area("Prompt", height=100, key='prompt')
            st.tokens_response = st.slider("Tokens response length", 100, 500, 400)
            st.temperature = st.slider("Temperature", 0.0, 1.0, 0.1)
            st.selectbox("Language", [None] + list(available_languages.keys()), key='translation_language')


    question = st.text_input("OpenAI Semantic Answer", default_question)

    if question != '':
        if question != st.session_state['question']:
            st.session_state['question'] = question
            # CAMBIO 4: Actualizar parámetro engine
            st.session_state['full_prompt'], st.session_state['response'], st.session_state['source_file'] = utils.get_semantic_answer(
                df, 
                question, 
                st.session_state['prompt'],
                model=model, 
                engine='gpt-35-turbo-instruct',  # Modelo actualizado
                tokens_response=st.tokens_response, 
                temperature=st.temperature
            )
            st.write(f"Q: {question}")  
            st.write(st.session_state['response']['choices'][0]['text'])
            with st.expander("Question and Answer Context"):
                st.text(st.session_state['full_prompt'].replace('$', '\$')) 
            if st.session_state['response']['choices'][0]['text'] == ' Not in the text.':
                st.session_state['source_file'] = ''
            else:
                st.write(st.session_state['source_file'])
            
        else:
            st.write(f"Q: {st.session_state['question']}")  
            st.write(f"{st.session_state['response']['choices'][0]['text']}")
            with st.expander("Question and Answer Context"):
                st.text(st.session_state['full_prompt'].encode().decode())
            if st.session_state['response']['choices'][0]['text'] == ' Not in the text.':
                st.session_state['source_file'] = ''
            else:
                st.write(st.session_state['source_file'])

    if st.session_state['translation_language'] is not None:
        st.write(f"Translation to other languages, 翻译成其他语言, النص باللغة العربية")
        st.write(f"{translator.translate(st.session_state['response']['choices'][0]['text'], available_languages[st.session_state['translation_language']])}")     
        
except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
        """
        % e.reason
    )