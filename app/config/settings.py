from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CLIENT_ID: str = "ABBUzqL6ULdbIHJXKENYjDHXXjizvSRmwxFr0eeFqMcHLmYxt1"
    CLIENT_SECRET: str = "YgzBiE9Ije7yBq7L2b9v08zBDkQxRlBVaKSPZiTl"
    REDIRECT_URI: str = "http://localhost:8000/callback"
    ENVIRONMENT: str = "sandbox"
    STATE: str = "random_string"
    
    # API URLs
    AUTH_BASE: str = "https://appcenter.intuit.com/connect/oauth2"
    TOKEN_URL: str = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    API_BASE: str = "https://sandbox-quickbooks.api.intuit.com/v3"
    
    # Database settings
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "quickbooks"
    
    class Config:
        env_file = ".env"

settings = Settings() 