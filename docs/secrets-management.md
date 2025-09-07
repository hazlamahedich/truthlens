# Secrets Management

This document outlines the process for managing secrets and environment variables for the TruthLens application, which uses a Next.js frontend and a FastAPI backend hosted on Vercel.

## 1. Vercel: The Source of Truth for Production

For all deployed environments (Production and Preview), Vercel is the single source of truth for environment variables.

- **Location:** Vercel Project > Settings > Environment Variables.
- **Activation:** You must create a new deployment for changes to take effect.

## 2. Local Development

For local development, we use a `.env.local` file at the root of the project.

- **Security:** This file is listed in `.gitignore` and should **never** be committed to version control.
- **Format:**
  ```
  # Server-only variable for Next.js
  API_SECRET_KEY="your-secret-key"

  # Public variable for Next.js (must be prefixed)
  NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"

  # Variable for FastAPI backend
  DATABASE_URL="your-database-url"
  ```

## 3. Accessing Variables in Next.js (Frontend)

- **Server-Side:** All environment variables are available on the server via `process.env.YOUR_VARIABLE_NAME`.
- **Client-Side:** To expose a variable to the browser, you **must** prefix it with `NEXT_PUBLIC_`. This is a security feature.

## 4. Accessing Variables in FastAPI (Backend)

We use Pydantic's Settings Management for type safety and validation.

1.  **Configuration:** A `config.py` file defines the settings and reads from environment variables and `.env` files.
2.  **Injection:** The settings are injected into the FastAPI application using a dependency.

### Example:

**`apps/api/config.py`**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DUMMY_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env.local")

@lru_cache()
def get_settings():
    return Settings()
```

**`apps/api/main.py`**
```python
from fastapi import FastAPI, Depends
from .config import Settings, get_settings

app = FastAPI()

@app.get("/api/some_endpoint")
def read_secret(settings: Settings = Depends(get_settings)):
    # You can now access your secret via settings.DUMMY_API_KEY
    return {"secret_status": "The dummy_api_key is configured"}
```
