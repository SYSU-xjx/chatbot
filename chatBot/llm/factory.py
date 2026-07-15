from langchain.chat_models import init_chat_model

from config.model_config import MODEL_CONFIG

def create_llm():
    return init_chat_model(
        MODEL_CONFIG["model"],
        model_provider=MODEL_CONFIG["provider"],
        api_key=MODEL_CONFIG["api_key"],
        base_url=MODEL_CONFIG["base_url"],
    )
