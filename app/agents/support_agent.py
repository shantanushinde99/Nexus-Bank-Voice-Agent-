from sqlalchemy.orm import Session
from app.tools.support_tools import create_support_ticket, transfer_to_human


class SupportAgent:
    """Specialized Agent for General Support and Escalations."""

    @staticmethod
    def process_request(db: Session, customer_id: str | None, intent: str, user_message: str) -> dict:
        msg_lower = user_message.lower()

        if "human" in intent or "agent" in msg_lower or "representative" in msg_lower or "escalate" in msg_lower or "person" in msg_lower:
            res = transfer_to_human(db, reason="Customer explicitly requested human agent", customer_id=customer_id)
            return {
                "agent": "SupportAgent",
                "tool_used": "transfer_to_human",
                "result": res,
                "response_text": res["message"],
            }

        else:
            res = create_support_ticket(db, customer_id, issue_description=user_message, category="Customer Support Inquiry")
            return {
                "agent": "SupportAgent",
                "tool_used": "create_support_ticket",
                "result": res,
                "response_text": f"I have logged a customer support ticket for your request (Ref #{res['ticket_id'][:8]}). Is there anything else I can help you with?",
            }
