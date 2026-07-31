# System Patterns: AI Voice Banking Assistant

## System Architecture

```
[ Customer Call (Voice) ]
         │
         ▼
    [ Vapi Platform ] ──(Webhook / Tool Calls)──► [ FastAPI Server ]
                                                          │
                                         ┌────────────────┴────────────────┐
                                         ▼                                 ▼
                              [ Vapi Webhook Route ]              [ REST Endpoints ]
                                         │                                 │
                                         ▼                                 │
                            [ Multi-Agent Coordinator ]                    │
                                         │                                 │
            ┌───────────────────┬────────┴──────────┬──────────────────┐   │
            ▼                   ▼                   ▼                  ▼   ▼
       [Auth Agent]       [Banking Agent]      [Loan Agent]      [Fraud Agent] [Support Agent]
            │                   │                   │                  │          │
            └───────────────────┴────────┬──────────┴──────────────────┴──────────┘
                                         ▼
                                  [ Tool Layer ]
                                         │ (Every tool creates AuditLog)
                                         ▼
                             [ SQLAlchemy ORM / DB ]
                                         │
                                         ▼
                               [ Supabase PostgreSQL ]
```

## Key Technical Patterns
1. **Layered Tool Architecture**:
   - Multi-agent layers interact ONLY via python functions in `app/tools/`.
   - Tool functions execute database ops, format Pydantic output, and auto-insert `AuditLog` records.

2. **Session & Auth State Management**:
   - In-memory / DB session state tracks `call_id`, `customer_id`, `authenticated`, and `failed_auth_attempts`.
   - Sensitive tools verify session authentication before performing actions.

3. **Vapi Protocol Adapter**:
   - Handles Vapi webhook payload structures (`function-call`, `tool-calls`, `assistant-request`).
   - Converts Vapi voice tool calls directly into python tool execution.

4. **Multi-Agent Intent Router**:
   - Coordinator agent uses Groq API / Google ADK models to analyze natural language, check intent, route to target sub-agent, or execute functions directly.
   - Includes robust rule-based mock routing engine fallback so test suite and offline demos execute seamlessly.
