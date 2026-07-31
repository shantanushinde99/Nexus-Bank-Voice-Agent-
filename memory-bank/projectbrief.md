# Project Brief: Production-Style AI Voice Banking Assistant

## Overview
Build a full-stack AI Voice Banking Assistant that simulates a real banking customer support system. This project demonstrates voice agents, multi-agent architecture, tool calling, secure authentication, API integration, database design, conversation memory, and human escalation using demo banking data (INR currency, Indian merchants & customer names).

## Goals
1. Greet callers and identify intent.
2. Securely authenticate customers using account last 4 digits and date of birth before revealing sensitive information.
3. Route customer inquiries to specialized agents (Coordinator, Auth, Banking, Loan, Fraud, Support).
4. Execute backend tools for banking actions (balance, transactions, card blocking, account freezing, EMI calculation, loan eligibility, support tickets).
5. Maintain conversational context across turn taking.
6. Escalate to human support when rules trigger (auth failure 3x, explicit request, fraud, tool error).
7. Record comprehensive audit logs for every tool invocation.

## Tech Stack
- **Language & Runtime**: Python 3.12
- **Framework**: FastAPI (Async REST endpoints & Vapi webhooks)
- **Agent Orchestration**: Multi-agent design (Google ADK / Groq LLM integration with fallback)
- **Database**: Supabase PostgreSQL / SQLAlchemy 2.0 ORM with SQLite local fallback support
- **Schema & Validation**: Pydantic v2
- **Voice Integration**: Vapi Webhook payload parsing and tool-calling protocol
- **Containerization**: Docker & Docker Compose
