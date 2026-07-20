from config.settings import get_env

MODEL_CONFIG = {
    "provider": "openai",
    "model": "glm-4.5-air",
    "base_url": "https://open.bigmodel.cn/api/paas/v4/",
    "api_key": get_env("OPENAI_API_KEY"),
}
