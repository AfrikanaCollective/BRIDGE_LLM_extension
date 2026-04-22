"""
Configuration for Qwen API Service
"""

import os
from typing import Optional


class Config:
    """Application configuration"""

    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://172.17.0.1:11434"
    )

    # Model settings
    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "qwen3.5:9b"
    )

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8443"))
    API_TITLE: str = os.getenv("API_TITLE", "Qwen API Service")
    API_VERSION: str = os.getenv("API_VERSION", "1.1.0")

    # SSL/TLS settings
    USE_HTTPS: bool = os.getenv("USE_HTTPS", "True").lower() in ("true", "1", "yes")
    SSL_CERT_FILE: str = os.getenv("SSL_CERT_FILE", "./certs/certificate.crt")
    SSL_KEY_FILE: str = os.getenv("SSL_KEY_FILE", "./certs/private.key")
    SSL_VERIFY: bool = os.getenv("SSL_VERIFY", "False").lower() in ("true", "1", "yes")

    # Concurrency settings
    MAX_CONCURRENT_REQUESTS: int = int(
        os.getenv("MAX_CONCURRENT_REQUESTS", "10")
    )
    REQUEST_TIMEOUT: int = int(
        os.getenv("REQUEST_TIMEOUT", "300")
    )

    # Image settings
    MAX_IMAGE_SIZE_MB: int = int(
        os.getenv("MAX_IMAGE_SIZE_MB", "10")
    )
    ALLOWED_IMAGE_FORMATS: tuple = tuple(
        os.getenv("ALLOWED_IMAGE_FORMATS", "JPEG,PNG,GIF,WEBP").split(",")
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def api_url(self) -> str:
        """Dynamically build API URL based on USE_HTTPS setting"""
        protocol = "https" if self.USE_HTTPS else "http"
        return f"{protocol}://{self.API_HOST}:{self.API_PORT}"


# For convenience, expose config as module-level variables
OLLAMA_BASE_URL = Config.OLLAMA_BASE_URL
MODEL_NAME = Config.MODEL_NAME
API_HOST = Config.API_HOST
API_PORT = Config.API_PORT
USE_HTTPS = Config.USE_HTTPS
SSL_CERT_FILE = Config.SSL_CERT_FILE
SSL_KEY_FILE = Config.SSL_KEY_FILE
SSL_VERIFY = Config.SSL_VERIFY
MAX_CONCURRENT_REQUESTS = Config.MAX_CONCURRENT_REQUESTS
REQUEST_TIMEOUT = Config.REQUEST_TIMEOUT
LOG_LEVEL = Config.LOG_LEVEL