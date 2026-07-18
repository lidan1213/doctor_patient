from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "mysql+aiomysql://medagent:medagent123@localhost:3306/medagent"
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "medagent"

    # Model adapters
    dashscope_api_key: str = ""
    ollama_host: str = "http://localhost:11434"

    # Model routing: "dashscope" | "ollama" | "auto" (dashscope first, ollama fallback)
    inference_backend: str = "auto"
    embedding_backend: str = "ollama"
    reranker_backend: str = "ollama"

    # MCP
    mcp_enabled: bool = True
    mcp_default_timeout: float = 10.0

    # Doubao (火山引擎) multimodal
    doubao_api_key: str = ""
    doubao_app_id: str = ""
    doubao_access_token: str = ""
    doubao_voice_resource_id_stt: str = "volc.bigasr.sauc.duration"
    doubao_voice_resource_id_tts: str = ""
    doubao_tts_model: str = "seed-audio-1.0"

    # MinIO
    minio_bucket_reports: str = "medagent-reports"
    max_upload_size_mb: int = 20

    # JWT
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # App
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:80", "http://localhost"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
