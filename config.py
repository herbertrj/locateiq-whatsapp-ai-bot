import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME')
OPENAI_MODEL_TEMPERATURE = float(os.getenv('OPENAI_MODEL_TEMPERATURE', 0))

AI_CONTEXTUALIZE_PROMPT = os.getenv('AI_CONTEXTUALIZE_PROMPT')
AI_SYSTEM_PROMPT = os.getenv('AI_SYSTEM_PROMPT')

VECTOR_STORE_PATH = os.getenv('VECTOR_STORE_PATH')
RAG_FILES_DIR = os.getenv('RAG_FILES_DIRS')

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME')
EVOLUTION_AUTHENTICATION_API_KEY = os.getenv('AUTHENTICATION_API_KEY')

REDIS_URL = os.getenv('CACHE_REDIS_URI')


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == '':
        return default
    try:
        return int(raw)
    except ValueError:
        return default


BUFFER_KEY_SUFIX = os.getenv('BUFFER_KEY_SUFIX', ':msgbuf')
DEBOUNCE_SECONDS = _int_env(
    'DEBOUNCE_SECONDS',
    _int_env('DEBALANCE_SECONDS', 5),
)
BUFFER_TTL = _int_env('BUFFER_TTL', 600)