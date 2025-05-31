import pandas as pd
import numpy as np
import openai
import os, io, zipfile
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from utilities.redisembeddings import execute_query, get_documents, set_document
from utilities.formrecognizer import analyze_read
from utilities.azureblobstorage import upload_file, upsert_blob_metadata
import tiktoken
import logging
import time
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa la conexión con la API de OpenAI
def initialize(engine='gpt-35-turbo-instruct'):
    """
    Configura los parámetros de conexión a la API de Azure OpenAI
    con verificación de credenciales
    """
    try:
        openai.api_type = "azure"
        openai.api_base = os.getenv('OPENAI_API_BASE')  # URL del endpoint
        openai.api_version = os.getenv("OPENAI_API_VERSION", "2024-05-01-preview")  # Versión actualizada
        openai.api_key = os.getenv("OPENAI_API_KEY")  # Clave de API
        
        # Verificar conexión
        models = openai.Model.list()
        logger.info(f"Conexión exitosa con OpenAI. Modelos disponibles: {len(models.data)}")
        return True
    except Exception as e:
        logger.error(f"Error inicializando OpenAI: {str(e)}")
        return False

# Calcula la similitud coseno entre dos vectores
def cosine_similarity(a, b):
    """
    Calcula la similitud coseno entre dos vectores de embeddings
    con manejo de división por cero
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return np.dot(a, b) / (norm_a * norm_b)

# Búsqueda semántica usando Redis
def search_semantic_redis(search_query, n=3, pprint=True):
    """
    Realiza una búsqueda semántica usando Redis como backend
    con manejo de errores robusto
    """
    try:
        # Obtiene embedding de la consulta
        embedding = get_embedding(search_query, engine=get_embeddings_model()['query'])
        
        # Ejecuta la consulta en Redis
        start_time = time.time()
        res = execute_query(np.array(embedding), n_results=n)
        duration = time.time() - start_time
        
        logger.info(f"Búsqueda semántica completada en {duration:.2f}s. Resultados: {len(res)}")
        
        if pprint and res:
            for doc in res[:3]:
                preview = doc['text'][:200].replace('\n', ' ')
                logger.info(f"Documento: {doc['filename']} | Preview: {preview}...")
                
        return res
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {str(e)}")
        return []

# Obtiene una respuesta semántica usando el modelo de OpenAI
def get_semantic_answer(question, explicit_prompt="", model="gpt-35-turbo-instruct", tokens_response=400, temperature=0.0):
    """
    Genera una respuesta a una pregunta usando contexto relevante
    con manejo de errores y optimización de prompt
    """
    try:
        start_time = time.time()
        
        # Paso 1: Buscar documentos relevantes en Redis
        res = search_semantic_redis(question, n=3, pprint=False)
        
        # Paso 2: Construir el prompt
        if not res:
            prompt = f"{question}"
            source_files = ['No se encontraron fuentes']
            logger.warning("No se encontraron documentos relevantes para la pregunta")
        else:
            # Combinar textos relevantes
            n_chunks = min(int(os.getenv("NUMBER_OF_EMBEDDINGS_FOR_QNA", 3)), len(res))
            res_text = "\n\n".join([doc['text'] for doc in res[:n_chunks]])
            
            # Obtener nombres de archivos fuente
            source_files = "Fuentes:\n" + "\n".join([f"- {doc['filename']}" for doc in res[:n_chunks]])
            
            # Preparar el prompt con la pregunta
            question_prompt = explicit_prompt.replace(r'\n', '\n').replace("_QUESTION_", question)
            prompt = f"Contexto:\n{res_text}\n\n---\n\n{question_prompt}"
        
        # Paso 3: Llamar a la API de OpenAI
        logger.info(f"Enviando prompt a OpenAI ({len(prompt)} caracteres)...")
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
        
        # Paso 4: Procesar la respuesta
        if response and response.choices:
            answer = response.choices[0].text.strip()
            logger.info(f"Respuesta generada: {answer[:100]}...")
            
            # Paso 5: Registrar métricas
            duration = time.time() - start_time
            logger.info(f"Proceso completado en {duration:.2f}s")
            
            return prompt, response, source_files
        else:
            logger.error("Respuesta vacía de OpenAI")
            return prompt, None, source_files
            
    except openai.error.RateLimitError:
        logger.error("Límite de tasa alcanzado. Espere y reintente.")
        raise
    except openai.error.APIError as e:
        logger.error(f"Error de API de OpenAI: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise

# Obtiene embeddings para un texto con reintentos automáticos
@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(8), 
       retry=retry_if_exception_type(openai.error.APIError))
def get_embedding(text: str, engine="text-embedding-ada-002") -> list[float]:
    """
    Obtiene el embedding vectorial para un texto con manejo robusto de errores
    y validación de entrada
    """
    try:
        # Validar y limpiar texto
        if not text or len(text.strip()) < 3:
            logger.warning("Texto vacío para embedding")
            return []
            
        text = clean_text(text)
        token_count = len(tiktoken.get_encoding('cl100k_base').encode(text))
        
        # Manejar textos demasiado largos
        if token_count > 8191:
            logger.warning(f"Texto demasiado largo ({token_count} tokens), truncando")
            text = text[:8000]  # Simple truncamiento para casos extremos
            
        logger.info(f"Solicitando embedding para {token_count} tokens")
        
        # Obtener embedding con tiempo de espera
        response = openai.Embedding.create(
            input=[text],
            engine=engine
        )
        
        return response["data"][0]["embedding"]
        
    except openai.error.InvalidRequestError as e:
        logger.error(f"Error en solicitud: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error obteniendo embedding: {str(e)}")
        raise

# Limpia texto para procesamiento
def clean_text(text: str) -> str:
    """
    Limpia el texto eliminando caracteres problemáticos
    y normalizando espacios
    """
    # Eliminar caracteres no ASCII (opcional, comentar si se necesitan caracteres internacionales)
    # text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Reemplazar múltiples espacios/newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Eliminar espacios al inicio/final
    return text.strip()

# Procesa y genera embeddings para un texto
def chunk_and_embed(text: str, filename=""):
    """
    Divide un texto en chunks y genera embeddings
    con manejo de textos largos
    """
    try:
        logger.info(f"Procesando documento: {filename}")
        
        # Limpiar y validar texto
        text = clean_text(text)
        if not text:
            logger.warning("Texto vacío después de limpieza")
            return None
        
        # Calcular tokens
        encoding = tiktoken.get_encoding('cl100k_base')
        tokens = encoding.encode(text)
        token_count = len(tokens)
        
        # Manejar textos largos dividiéndolos
        if token_count > 3000:
            logger.info(f"Dividiendo texto largo ({token_count} tokens)")
            chunks = []
            chunk_size = 2000  # Tokens por chunk
            
            for i in range(0, token_count, chunk_size):
                chunk_text = encoding.decode(tokens[i:i+chunk_size])
                chunk_text = clean_text(chunk_text)
                
                if not chunk_text:
                    continue
                    
                embedding = get_embedding(chunk_text)
                chunks.append({
                    "text": chunk_text,
                    "filename": f"{filename}_part_{i//chunk_size}",
                    "embedding": embedding
                })
            
            logger.info(f"Texto dividido en {len(chunks)} chunks")
            return chunks
            
        # Texto normal
        else:
            embedding = get_embedding(text)
            return {
                "text": text,
                "filename": filename,
                "embedding": embedding
            }
            
    except Exception as e:
        logger.error(f"Error en chunk_and_embed: {str(e)}")
        return None

# Añade embeddings a la base de datos
def add_embeddings(text, filename):
    """
    Procesa un texto y guarda sus embeddings en Redis
    con manejo de múltiples chunks
    """
    try:
        embeddings = chunk_and_embed(text, filename)
        if not embeddings:
            logger.warning("No se generaron embeddings")
            return False
            
        # Manejar múltiples chunks
        if isinstance(embeddings, list):
            for item in embeddings:
                set_document(item)
            logger.info(f"Embeddings guardados ({len(embeddings)} chunks)")
            return True
        else:
            set_document(embeddings)
            logger.info("Embedding guardado")
            return True
            
    except Exception as e:
        logger.error(f"Error añadiendo embeddings: {str(e)}")
        return False

# Procesa un archivo, lo convierte y genera embeddings
def convert_file_and_add_embeddings(fullpath, filename):
    """
    Convierte un archivo a texto, lo divide en chunks
    y genera embeddings para cada chunk con manejo de errores
    """
    try:
        logger.info(f"Procesando archivo: {filename}")
        start_time = time.time()
        
        # Paso 1: Extraer texto del archivo
        text_chunks = analyze_read(fullpath)
        if not text_chunks:
            logger.error("No se pudo extraer texto del archivo")
            return False
            
        # Paso 2: Crear archivo ZIP con los chunks de texto
        zip_file = io.BytesIO()
        with zipfile.ZipFile(zip_file, mode="w") as archive:
            for i, chunk in enumerate(text_chunks):
                archive.writestr(f"chunk_{i}.txt", chunk)
        
        # Paso 3: Subir ZIP a Azure Blob Storage
        upload_file(zip_file.getvalue(), f"converted/{filename}.zip", content_type='application/zip')
        upsert_blob_metadata(filename, {"converted": "true", "chunks": str(len(text_chunks))})
        
        # Paso 4: Procesar cada chunk de texto
        total_chunks = 0
        for i, chunk in enumerate(text_chunks):
            # Limpiar y validar chunk
            chunk = clean_text(chunk)
            if not chunk:
                continue
                
            # Procesar chunk
            if add_embeddings(chunk, f"{filename}_chunk_{i}"):
                total_chunks += 1
        
        # Registrar resultados
        duration = time.time() - start_time
        logger.info(f"Archivo procesado: {total_chunks} chunks en {duration:.2f}s")
        return total_chunks > 0
        
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        return False

# Obtiene configuración de modelos de embeddings
def get_embeddings_model():
    """
    Obtiene los modelos de embeddings configurados
    con valores por defecto seguros
    """
    return {
        "doc": os.getenv('OPENAI_EMBEDDINGS_ENGINE_DOC', 'text-embedding-ada-002'),
        "query": os.getenv('OPENAI_EMBEDDINGS_ENGINE_QUERY', 'text-embedding-ada-002')
    }

# Genera texto a partir de un prompt con manejo de errores
def get_completion(prompt="", max_tokens=400, model="gpt-35-turbo-instruct"):
    """
    Genera texto de continuación para un prompt
    con manejo de errores robusto
    """
    try:
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
        return response.choices[0].text.strip() if response.choices else ""
    except Exception as e:
        logger.error(f"Error en get_completion: {str(e)}")
        return ""

# Cuenta tokens en un texto eficientemente
def get_token_count(text: str):
    """
    Calcula el número de tokens en un texto
    usando la misma codificación que para embeddings
    """
    try:
        encoding = tiktoken.get_encoding('cl100k_base')
        return len(encoding.encode(clean_text(text)))
    except:
        return 0