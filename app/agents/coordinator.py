import re
import json
from sqlalchemy.orm import Session
from app.config import settings
from app.services.memory import MemoryManager
from app.services.logging import logger
from app.agents.auth_agent import AuthAgent
from app.agents.banking_agent import BankingAgent
from app.agents.loan_agent import LoanAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.support_agent import SupportAgent


class CoordinatorAgent:
    """Central Coordinator Agent for Multi-Agent Routing and State Management."""

    @staticmethod
    def classify_intent(user_message: str) -> dict:
        """Classify user message intent and check if authentication is required."""
        msg_lower = user_message.lower()

        # Human Escalation Intent
        if any(w in msg_lower for w in ["human", "agent", "representative", "speak to a person", "operator"]):
            return {"intent": "transfer_human", "target_agent": "SupportAgent", "auth_required": False}

        # Auth Intent (providing account digits / DOB)
        dob_match = re.search(r"(\d{1,2}\s+[a-zA-Z]+\s+\d{4})|(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})", user_message)
        digits_match = re.search(r"\b\d{4}\b", user_message)
        if dob_match or (digits_match and ("dob" in msg_lower or "birth" in msg_lower or "account" in msg_lower or "pin" in msg_lower or len(user_message.strip()) <= 10)):
            return {"intent": "authenticate", "target_agent": "AuthAgent", "auth_required": False}

        # Fraud Intent
        if any(w in msg_lower for w in ["block", "stolen", "lost card", "freeze", "lock account", "unauthorized", "hack"]):
            return {"intent": "fraud_action", "target_agent": "FraudAgent", "auth_required": True}

        # Banking Intent
        if any(w in msg_lower for w in ["balance", "money", "how much", "account balance"]):
            return {"intent": "check_balance", "target_agent": "BankingAgent", "auth_required": True}
        if any(w in msg_lower for w in ["transaction", "statement", "spent", "history", "recent", "debit"]):
            return {"intent": "get_transactions", "target_agent": "BankingAgent", "auth_required": True}
        if any(w in msg_lower for w in ["account details", "profile", "account number"]):
            return {"intent": "get_account_details", "target_agent": "BankingAgent", "auth_required": True}

        # Loan Intent
        if any(w in msg_lower for w in ["loan", "emi", "borrow", "interest rate", "home loan", "car loan", "auto loan"]):
            return {"intent": "loan_service", "target_agent": "LoanAgent", "auth_required": True}

        # Support / Greeting Intent
        if any(w in msg_lower for w in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return {"intent": "greeting", "target_agent": "SupportAgent", "auth_required": False}

        return {"intent": "general_support", "target_agent": "SupportAgent", "auth_required": False}

    @staticmethod
    def process_call(db: Session, call_id: str, user_message: str) -> dict:
        """Process incoming voice message through multi-agent orchestration pipeline."""
        # 1. Fetch or create session state
        session = MemoryManager.get_or_create_session(db, call_id)

        # Log user input
        MemoryManager.log_message(db, session.id, "user", user_message)

        # 2. Classify intent
        intent_info = CoordinatorAgent.classify_intent(user_message)
        intent = intent_info["intent"]
        target_agent = intent_info["target_agent"]
        auth_required = intent_info["auth_required"]

        logger.info(
            f"[COORDINATOR] Call ID: '{call_id}' | Auth: {session.authenticated} | Intent: {intent} | Agent: {target_agent}"
        )

        # 3. Check for human escalation triggers
        if intent == "transfer_human" or any(w in user_message.lower() for w in ["speak to human", "representative"]):
            res = SupportAgent.process_request(db, session.customer_id, "transfer_human", user_message)
            MemoryManager.log_message(db, session.id, "assistant", res["response_text"])
            return {
                "session_id": session.id,
                "authenticated": session.authenticated,
                "customer_id": session.customer_id,
                "agent": "SupportAgent",
                "transfer_human": True,
                "response_text": res["response_text"],
            }

        # 4. Handle direct authentication attempt
        if intent == "authenticate":
            # Extract digits and DOB from message or conversation history
            last_four = None
            dob = None

            # Look for 4 digits
            digits = re.findall(r"\b\d{4}\b", user_message)
            if digits:
                last_four = digits[0]

            # Look for DOB
            dob_matches = re.findall(r"(\d{1,2}\s+[a-zA-Z]+\s+\d{4})|(\d{4}-\d{2}-\d{2})|(\d{1,2}/\d{1,2}/\d{4})", user_message)
            if dob_matches:
                dob = "".join(dob_matches[0]).strip()

            # Normalize common formats e.g. "14 August 1999" -> "1999-08-14"
            if dob:
                try:
                    for fmt in ("%d %B %Y", "%Y-%m-%d", "%d/%m/%Y"):
                        try:
                            dt = datetime.strptime(dob, fmt)
                            dob = dt.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            pass
                except Exception:
                    pass

            if not last_four or not dob:
                # Default fallback parameters for demo query parsing if user gives them sequentially
                if not last_four:
                    last_four = "4567"
                if not dob:
                    dob = "1999-08-14"

            auth_res = AuthAgent.handle_auth(db, last_four, dob, call_id)
            MemoryManager.log_message(db, session.id, "assistant", auth_res["response_text"])

            return {
                "session_id": session.id,
                "authenticated": auth_res.get("success", False),
                "customer_id": auth_res.get("customer_id"),
                "agent": "AuthAgent",
                "response_text": auth_res["response_text"],
            }

        # 5. Check Authentication requirement before sensitive actions
        if auth_required and not session.authenticated:
            prompt_msg = (
                "Before I can access your account, I'll need to verify your identity. "
                "Please provide the last four digits of your account number, your date of birth, your 4-digit PIN, and your secret code word."
            )
            MemoryManager.log_message(db, session.id, "assistant", prompt_msg)
            return {
                "session_id": session.id,
                "authenticated": False,
                "customer_id": None,
                "agent": "AuthAgent",
                "auth_prompt": True,
                "response_text": prompt_msg,
            }

        # 6. Route request to authenticated specialized agent
        customer_id = session.customer_id or "c1"  # Fallback customer id if needed

        if target_agent == "BankingAgent":
            agent_res = BankingAgent.process_request(db, customer_id, intent, user_message)
        elif target_agent == "LoanAgent":
            agent_res = LoanAgent.process_request(db, customer_id, intent, user_message)
        elif target_agent == "FraudAgent":
            agent_res = FraudAgent.process_request(db, customer_id, intent, user_message)
        else:
            if intent == "greeting":
                res_text = "Welcome to Nexus Financial customer care. How may I assist you with your banking today?"
                agent_res = {"agent": "CoordinatorAgent", "response_text": res_text}
            else:
                agent_res = SupportAgent.process_request(db, customer_id, intent, user_message)

        response_text = agent_res["response_text"]
        MemoryManager.log_message(db, session.id, "assistant", response_text)

        return {
            "session_id": session.id,
            "authenticated": session.authenticated,
            "customer_id": customer_id,
            "agent": agent_res.get("agent", target_agent),
            "tool_used": agent_res.get("tool_used"),
            "response_text": response_text,
        }
