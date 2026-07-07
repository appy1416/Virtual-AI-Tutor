import os
from typing import List
import json

# Minimal .env loader helper to avoid dependency issues
def load_dotenv(env_path: str = ".env"):
    if not os.path.exists(env_path):
        # Try parent directory
        env_path = os.path.join("..", env_path)
        if not os.path.exists(env_path):
            return
            
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip()
                    # Strip quotes if present
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass

# Load environment variables
load_dotenv()

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "EduTwin AI")
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me_to_a_secure_random_hex_string_in_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:appy1416@localhost:5432/edutwin_db"
    )
    
    # SMTP & Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Groq AI settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_CHAT_MODEL: str = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
    
    # CORS
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        origins = os.getenv("BACKEND_CORS_ORIGINS")
        if origins:
            try:
                return json.loads(origins)
            except Exception:
                return [o.strip() for o in origins.split(",")]
        return [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002"
        ]

settings = Settings()

