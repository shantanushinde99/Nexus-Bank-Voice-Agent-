# 🏦 Production-Style AI Voice Banking Assistant

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Vapi Voice](https://img.shields.io/badge/Vapi-Voice--AI-purple.svg)](https://vapi.ai/)
[![Model](https://img.shields.io/badge/LLM-openai%2Fgpt--4o--mini-orange.svg)](https://openai.com/)

An end-to-end, production-grade AI Voice Banking Assistant simulating a real customer support system. Demonstrates **Voice Agent Webhooks (Vapi)**, **Multi-Agent Coordination (Custom Python Orchestration & Groq/OpenAI LLMs)**, **Function Tool Calling**, **Customer Identity Verification**, **Audit Logging**, **Conversation Memory**, and **Human Escalation**.

> [!IMPORTANT]
> **Demo Banking Data Only**: This system operates using mock Indian banking records (INR currency ₹, simulated account numbers, realistic merchants). It never connects to any real financial institution.

---

## 📐 Architecture & Workflow Diagram

```mermaid
graph TD
    %% Caller Interaction
    Caller([📞 Customer Call]) <-->|Spoken Audio| Vapi[🎙️ Vapi AI Platform]
    
    subgraph "Vapi Cloud"
        Vapi <-->|Context & Prompts| LLM[🧠 LLM Provider <br> e.g., GPT-4o Mini]
        Vapi <-->|STT / TTS| Transcriber[Deepgram Nova-2]
    end

    %% Webhook Integration
    Vapi -->|Webhook HTTP POST <br> Function Call Request| FastAPI[⚡ FastAPI Backend Server]
    FastAPI -->|JSON Tool Response| Vapi

    subgraph "Backend System (FastAPI + AI Agents)"
        FastAPI --> Coordinator[🎯 Coordinator Agent <br> State & Intent Manager]
        
        Coordinator -->|Intent: Identity| AuthAgent[🛡️ Auth Agent]
        Coordinator -->|Intent: Account| BankAgent[🏦 Banking Agent]
        Coordinator -->|Intent: Credit| LoanAgent[💳 Loan Agent]
        Coordinator -->|Intent: Security| FraudAgent[🚨 Fraud Agent]
        Coordinator -->|Intent: General| SupportAgent[🎧 Support Agent]
    end

    subgraph "Data & Persistence Layer"
        AuthAgent --> Tools[🛠️ Backend Tools Layer]
        BankAgent --> Tools
        LoanAgent --> Tools
        FraudAgent --> Tools
        SupportAgent --> Tools
        
        Tools <--> DB[(🗄️ Supabase PostgreSQL)]
        Tools -->|Auto Logging| Audit[📝 Audit Logs Table]
    end

    style Vapi fill:#6f42c1,stroke:#333,stroke-width:2px,color:#fff
    style FastAPI fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    style Coordinator fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff
    style DB fill:#336791,stroke:#333,stroke-width:2px,color:#fff
```

---

## 🧠 Deep Dive: How the System Works

### 1. How the Agent Operates (Multi-Agent Architecture)

```mermaid
sequenceDiagram
    participant User
    participant Coordinator
    participant AuthAgent
    participant BankAgent
    
    User->>Coordinator: "What is my balance?" (Intent: check_balance)
    Coordinator->>Coordinator: Check Session State (Authenticated?)
    
    alt Not Authenticated
        Coordinator->>AuthAgent: Route to AuthAgent
        AuthAgent->>User: "Please provide last 4 digits of account and DOB."
        User->>AuthAgent: "1234, 15 March 1990"
        AuthAgent->>Coordinator: Verification Success
        Coordinator->>Coordinator: Update Session State = Authenticated
    end
    
    Coordinator->>BankAgent: Route to BankingAgent (with intent & ID)
    BankAgent->>User: "Your balance is ₹15,000."
```

Instead of relying on a single monolithic prompt, this system uses a **Coordinator-Subagent pattern**:
- **Coordinator Agent**: When a call connects, the Coordinator determines the caller's intent. It tracks session context, handles the conversation state, and routes the request to the appropriate subagent.
- **Subagents**: Specialized agents handle distinct domains. 
  - *Authentication Agent* enforces security (asking for the last 4 digits of the account and DOB).
  - *Banking Agent* handles balances and transactions.
  - *Fraud Agent* manages high-risk actions like blocking cards or freezing accounts.
- **Memory & State**: Once a caller is verified by the Auth Agent, the Coordinator stores this authentication state. Subsequent requests (like transferring funds or checking balances) bypass the security checks seamlessly.

### 2. How Tool Calling Works

```mermaid
sequenceDiagram
    participant Vapi as Vapi Cloud (STT/LLM/TTS)
    participant API as FastAPI Webhook
    participant Function as Python Tool Logic
    
    Vapi->>Vapi: LLM decides it needs real-time data
    Vapi->>API: HTTP POST /api/vapi/webhook <br/> JSON: {"message": {"toolCalls": [{"name": "get_balance"}]}}
    API->>Function: Execute get_balance(customer_id)
    Function-->>API: Returns: {"balance": 15000, "currency": "INR"}
    API-->>Vapi: HTTP 200 OK <br/> JSON: {"results": [{"result": "Balance is 15000 INR"}]}
    Vapi->>Vapi: LLM generates conversational response
    Vapi-->>User: (Spoken) "You have ₹15,000 in your account."
```

The AI interacts with the real world using **Function Tool Calling**:
- **Vapi Integration**: The Vapi AI platform listens to the user and converts speech to text. If the LLM decides it needs real-time data (e.g., checking a balance), it triggers a *Tool Call*.
- **Webhook Execution**: Vapi sends an HTTP POST request to our FastAPI backend (`/api/vapi/webhook` or specific tool endpoints like `/api/balance/{id}`).
- **Backend Processing**: FastAPI validates the incoming JSON payload using Pydantic, executes the requested Python function (e.g., querying the database), and returns a JSON response.
- **Voice Response**: Vapi feeds the JSON response back to the LLM, which translates the raw data into natural, conversational speech for the caller (e.g., *"Your balance is ₹15,000"*).

### 3. How Data Fetching Works

```mermaid
graph LR
    Tool[Function Execution<br>e.g., block_card] --> Interceptor{Audit Decorator}
    Interceptor -->|1. Write| AuditLog[(AuditLog Table)]
    Interceptor -->|2. Continue| Logic[Core Business Logic]
    Logic <-->|SQLAlchemy ORM| DB[(Supabase PostgreSQL)]
    DB -.->|Offline Fallback| SQLite[(Local SQLite)]
```

The system persists data securely and efficiently:
- **Supabase PostgreSQL**: The primary database hosted in the cloud. It stores structured data like `Customers`, `Accounts`, `Cards`, `Loans`, and `Transactions`.
- **SQLAlchemy ORM**: We use SQLAlchemy 2.0 to safely map Python objects to database tables, preventing SQL injection and abstracting complex queries.
- **Audit Logging**: Every time a tool is executed (e.g., a card is blocked or balance is checked), a decorator function automatically intercepts the action and writes an immutable record to the `AuditLog` table. This is critical for banking compliance.
- **Local Fallback**: If Supabase is unavailable, the system seamlessly falls back to a local SQLite database (`voice_bank.db`) using the same ORM models.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn
- **Voice Platform**: Vapi Webhook integration
- **Transcriber/TTS**: Deepgram (Nova-2, multi-language support) / OpenAI TTS
- **Multi-Agent LLM**: OpenAI GPT-4o Mini / Groq (`llama3-70b-8192`)
- **Database & ORM**: Supabase PostgreSQL / SQLAlchemy 2.0 (with SQLite local fallback)
- **Data Validation**: Pydantic v2
- **Containerization**: Docker & Docker Compose

---

## ⚙️ Environment Variables

Create a `.env` file from `.env.example`:

```env
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development

# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=openai/gpt-4o-mini

# Supabase / Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Vapi Integration
VAPI_API_KEY=your_vapi_private_api_key_here
VAPI_PUBLIC_KEY=your_vapi_public_key_here
VAPI_ASSISTANT_ID=your_vapi_assistant_id_here
VAPI_WEBHOOK_SECRET=your_vapi_webhook_secret_here
```

---

## 🚀 Running Locally

### Option 1: Virtual Environment (.venv)

```bash
# 1. Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed demo database with realistic Indian banking records
python -m app.database.seed

# 4. Start FastAPI server
uvicorn app.main:app --port 8000 --reload
```

### Option 2: Docker Compose

```bash
docker-compose up --build
```

Access Interactive API Documentation at: `http://localhost:8000/docs`

---

## 🌐 Setting Up Ngrok (Local Tunnel)

To connect Vapi to your local environment, you need a public URL that forwards to your localhost. We use **Ngrok** for this.

### 1. Download & Authenticate
1. Create a free account at [ngrok.com](https://ngrok.com/)
2. Download the Ngrok executable and place it in the project root folder.
3. Authenticate your agent (run this once):
   ```bash
   .\ngrok.exe config add-authtoken YOUR_NGROK_TOKEN
   ```

### 2. Claim a Static Domain (Free)
Ngrok now offers free static domains, which means you don't have to update Vapi every time you restart!
1. Go to your Ngrok Dashboard -> **Domains**
2. Click **Create Domain** (e.g., `rental-hardy-exerciser.ngrok-free.dev`)

### 3. Run the Servers (Automated Script)
We have provided a PowerShell script that simultaneously launches both your FastAPI backend and the Ngrok tunnel using your static domain.

1. Open `start_all.ps1` and ensure the `--domain` matches your claimed static domain.
2. Run the script in PowerShell:
   ```powershell
   .\start_all.ps1
   ```
This will give you a permanent Public Webhook URL (e.g., `https://rental-hardy-exerciser.ngrok-free.dev/api/vapi/webhook`).

---

## 📞 Connecting Vapi Voice Platform

1. Create a custom assistant on [Vapi Dashboard](https://dashboard.vapi.ai/).
2. Set Server Webhook URL to: `https://<your-domain-or-ngrok>/api/vapi/webhook`.
3. Register backend function tools:
   - `verify_customer`
   - `get_balance`
   - `get_recent_transactions`
   - `block_card`
   - `freeze_account`
   - `check_loan_eligibility`
   - `calculate_emi`
   - `create_support_ticket`
   - `transfer_to_human`

---

## 🧪 Running Automated Tests

Run the complete pytest suite covering API endpoints, tools, audit logs, and multi-agent voice conversations:

```bash
.venv\Scripts\python -m pytest -v
```

---

## 📄 API Documentation Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status |
| `POST` | `/api/verify-user` | Authenticate customer identity |
| `GET` | `/api/balance/{customer_id}` | Retrieve account balances in INR (₹) |
| `GET` | `/api/transactions/{customer_id}` | Fetch recent transactions |
| `GET` | `/api/account/{customer_id}` | Fetch customer account profile |
| `POST` | `/api/block-card` | Block debit/credit card |
| `POST` | `/api/freeze-account` | Freeze customer accounts |
| `POST` | `/api/loan-eligibility` | Check loan eligibility & EMI capacity |
| `POST` | `/api/loan-request` | Submit loan application |
| `POST` | `/api/support-ticket` | Generate customer support ticket |
| `POST` | `/api/transfer-human` | Escalate call to human operator |
| `POST` | `/api/agent/chat` | Simulated interactive voice turn endpoint |
| `POST` | `/api/vapi/webhook` | Vapi voice platform webhook integration |
| `GET` | `/api/config` | Frontend configuration delivery |

---

## 🔮 Future Improvements

- OpenTelemetry distributed tracing across agent tool calls.
- Voice biometric authentication integration.
- Real-time customer sentiment detection & voice pitch analysis.
- Multi-lingual voice support (Hindi, Tamil, Telugu, Marathi).
