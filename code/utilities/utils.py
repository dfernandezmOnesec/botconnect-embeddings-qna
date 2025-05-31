import pandas as pd
import numpy as np
import openai
import os, io, zipfile
from tenacity import retry, wait_random_exponential, stop_after_attempt
from utilities.redisembeddings import execute_query, get_documents, set_document
from utilities.formrecognizer import analyze_read
from utilities.azureblobstorage import upload_file, upsert_blob_metadata
import tiktoken
import logging

# Inicializa la conexión con la API de OpenAI
def initialize(engine='gpt-35-turbo-instruct'):
    """
    Configura los parámetros de conexión a la API de Azure OpenAI
    """
    openai.api_type = "azure"
    openai.api_base = os.getenv('OPENAI_API_BASE')  # URL del endpoint
    openai.api_version = os.getenv("OPENAI_API_VERSION", "2023-12-01-preview")  # Versión de API
    openai.api_key = os.getenv("OPENAI_API_KEY")  # Clave de API

# Calcula la similitud coseno entre dos vectores
def cosine_similarity(a, b):
    """
    Calcula la similitud coseno entre dos vectores de embeddings
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Búsqueda semántica local usando embeddings
def search_semantic(df, search_query, n=3, pprint=True):
    """
    Realiza una búsqueda semántica en un DataFrame local
    usando embeddings precalculados
    
    Args:
        df: DataFrame con embeddings
        search_query: Consulta de búsqueda
        n: Número de resultados a devolver
        pprint: Si se muestran los resultados
    
    Returns:
        DataFrame con los resultados ordenados
    """
    # Obtiene el embedding de la consulta
    embedding = get_embedding(search_query, engine=get_embeddings_model()['query'])
    
    # Calcula similitudes
    df['similarities'] = df['embedding'].apply(lambda x: cosine_similarity(x, embedding))
    
    # Ordena y selecciona los mejores resultados
    res = df.sort_values('similarities', ascending=False).head(n)
    
    if pprint:
        for r in res:
            print(r[:200])  # Muestra un preview
            print()
    return res.reset_index()

# Búsqueda semántica usando Redis
def search_semantic_redis(search_query, n=3, pprint=True):
    """
    Realiza una búsqueda semántica usando Redis como backend
    
    Args:
        search_query: Consulta de búsqueda
        n: Número de resultados a devolver
        pprint: Si se muestran los resultados
    
    Returns:
        Lista de documentos relevantes
    """
    # Obtiene embedding de la consulta
    embedding = get_embedding(search_query, engine=get_embeddings_model()['query'])
    
    # Ejecuta la consulta en Redis
    res = execute_query(np.array(embedding))
    
    if pprint:
        for r in res:
            print(r[:200])  # Muestra un preview
            print()
    return res

# Obtiene una respuesta semántica usando el modelo de OpenAI
def get_semantic_answer(question, explicit_prompt="", model="gpt-35-turbo-instruct", tokens_response=400, temperature=0.0):
    """
    Genera una respuesta a una pregunta usando contexto relevante
    
    Args:
        question: Pregunta a responder
        explicit_prompt: Plantilla del prompt
        model: Modelo de OpenAI a usar
        tokens_response: Máximo de tokens en la respuesta
        temperature: Creatividad de la respuesta
    
    Returns:
        prompt: Prompt completo usado
        response: Respuesta de OpenAI
        source_files: Fuentes de información usadas
    """
    restart_sequence = "\n\n"
    
    # Paso 1: Buscar documentos relevantes en Redis
    res = search_semantic_redis(question, n=3, pprint=False)
    
    # Paso 2: Construir el prompt
    if len(res) == 0:
        prompt = f"{question}"
        source_files = ['No se encontraron fuentes']
    else:
        # Combinar textos relevantes
        res_text = "\n".join([doc['text'] for doc in res[:int(os.getenv("NUMBER_OF_EMBEDDINGS_FOR_QNA",1))]])
        
        # Obtener nombres de archivos fuente
        source_files = "Fuentes: \n" + "\n".join([doc['filename'] for doc in res[:int(os.getenv("NUMBER_OF_EMBEDDINGS_FOR_QNA",1))]])
        
        # Preparar el prompt con la pregunta
        question_prompt = explicit_prompt.replace(r'\n', '\n').replace("_QUESTION_", question)
        prompt = f"{res_text}{restart_sequence}{question_prompt}"
            
    # Paso 3: Llamar a la API de OpenAI
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=tokens_response,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    
    # Paso 4: Manejar la respuesta
    if response:
        print(f"Respuesta: {response['choices'][0]['text'].encode().decode()}\n\n")
        print(f"{source_files}")
    else:
        response = ''

    return prompt, response, source_files

# Obtiene embeddings para un texto con reintentos automáticos
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(text: str, engine="text-embedding-ada-002") -> list[float]:
    """
    Obtiene el embedding vectorial para un texto
    
    Args:
        text: Texto a procesar
        engine: Modelo de embeddings a usar
    
    Returns:
        Lista de floats representando el embedding
    """
    text = text.replace("\n", " ")  # Limpiar saltos de línea
    encoding = tiktoken.get_encoding('cl100k_base')  # Codificación para ADA-002
    return openai.Embedding.create(input=encoding.encode(text), engine=engine)["data"][0]["embedding"]

# Procesa y genera embeddings para un texto
def chunk_and_embed(text: str, filename=""):
    """
    Divide un texto en chunks y genera embeddings
    
    Args:
        text: Texto a procesar
        filename: Nombre del archivo origen
    
    Returns:
        Diccionario con texto, nombre y embedding
    """
    logging.info(f"Procesando documento: {filename}")
    encoding = tiktoken.get_encoding('cl100k_base')
    token_count = len(encoding.encode(text))
    
    # Validar longitud máxima
    if token_count > 8000:
        logging.warning(f"Documento demasiado largo ({token_count} tokens), omitiendo: {filename}")
        return None

    # Generar embedding
    embedding = get_embedding(text)
    return {
        "text": text,
        "filename": filename,
        "embedding": embedding
    }

# Genera texto a partir de un prompt
def get_completion(prompt="", max_tokens=400, model="gpt-35-turbo-instruct"):
    """
    Genera texto de continuación para un prompt
    
    Args:
        prompt: Texto inicial
        max_tokens: Máximo de tokens a generar
        model: Modelo a usar
    
    Returns:
        Texto generado
    """
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        temperature=0.7,
        max_tokens=max_tokens,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return response['choices'][0]['text'].strip()

# Cuenta tokens en un texto
def get_token_count(text: str):
    """
    Calcula el número de tokens en un texto
    
    Args:
        text: Texto a analizar
    
    Returns:
        Número de tokens
    """
    encoding = tiktoken.get_encoding('cl100k_base')
    return len(encoding.encode(text))

# Obtiene configuración de modelos de embeddings
def get_embeddings_model():
    """
    Obtiene los modelos de embeddings configurados
    
    Returns:
        Diccionario con modelos para documentos y consultas
    """
    return {
        "doc": os.getenv('OPENAI_EMBEDDINGS_ENGINE_DOC', 'text-embedding-ada-002'),
        "query": os.getenv('OPENAI_EMBEDDINGS_ENGINE_QUERY', 'text-embedding-ada-002')
    }

# Añade embeddings a la base de datos
def add_embeddings(text, filename):
    """
    Procesa un texto y guarda sus embeddings en Redis
    
    Args:
        text: Texto a procesar
        filename: Nombre del archivo origen
    
    Returns:
        True si tuvo éxito, False si falló
    """
    embeddings = chunk_and_embed(text, filename)
    if embeddings:
        set_document(embeddings)  # Guardar en Redis
        return True
    return False

# Procesa un archivo, lo convierte y genera embeddings
def convert_file_and_add_embeddings(fullpath, filename):
    """
    Convierte un archivo a texto, lo divide en chunks
    y genera embeddings para cada chunk
    
    Args:
        fullpath: Ruta completa al archivo
        filename: Nombre del archivo
    """
    # Paso 1: Extraer texto del archivo
    text_chunks = analyze_read(fullpath)
    zip_file = io.BytesIO()
    
    # Paso 2: Crear archivo ZIP con los chunks de texto
    with zipfile.ZipFile(zip_file, mode="a") as archive:
        for i, chunk in enumerate(text_chunks):
            archive.writestr(f"{i}.txt", chunk)
    
    # Paso 3: Subir ZIP a Azure Blob Storage
    upload_file(zip_file.getvalue(), f"converted/{filename}.zip", content_type='application/zip')
    upsert_blob_metadata(filename, {"converted": "true"})
    
    # Paso 4: Procesar cada chunk de texto
    max_chars = 3500  # Tamaño máximo por chunk
    for i, chunk in enumerate(text_chunks):
        # Dividir chunks grandes
        if len(chunk) > max_chars:
            for j in range(0, len(chunk), max_chars):
                sub_chunk = chunk[j:j+max_chars]
                add_embeddings(sub_chunk, f"{filename}_chunk_{i}_{j//max_chars}")
        else:
            add_embeddings(chunk, f"{filename}_chunk_{i}")