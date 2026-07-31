# Technical Context: AI Voice Banking Assistant

## Environment & Dependencies
- **Python**: 3.12.0
- **Dependencies**:
  - `fastapi`, `uvicorn`: Web framework & ASGI server
  - `sqlalchemy`, `psycopg2-binary`: Database ORM & PostgreSQL driver
  - `pydantic`, `pydantic-settings`: Data validation & configuration
  - `groq`: Groq API client
  - `google-genai`: Google GenAI / ADK SDK integration
  - `httpx`: Async HTTP client
  - `pytest`, `pytest-asyncio`: Automated testing
  - `python-dotenv`: Environment configuration

## Configurable Environment Variables
- `GROQ_API_KEY`: Groq API Key
- `MODEL_NAME`: Groq model string (e.g. `llama-3.3-70b-versatile`)
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase API key
- `DATABASE_URL`: SQLAlchemy connection string (`postgresql://...` or `sqlite:///./voice_bank.db`)
- `VAPI_API_KEY`: Vapi Private API Key
- `ENVIRONMENT`: `development` | `production` | `testing`
