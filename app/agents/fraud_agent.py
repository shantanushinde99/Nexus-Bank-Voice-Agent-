from sqlalchemy.orm import Session
from app.tools.fraud_tools import block_card, freeze_account


class FraudAgent:
    """Specialized Agent for Card Blocking and Account Freezing."""

    @staticmethod
    def process_request(db: Session, customer_id: str, intent: str, user_message: str) -> dict:
        msg_lower = user_message.lower()

        if "freeze" in intent or "freeze" in msg_lower or "lock account" in msg_lower:
            res = freeze_account(db, customer_id, reason="Customer reported security threat / fraud request")
            return {
                "agent": "FraudAgent",
                "tool_used": "freeze_account",
                "result": res,
                "response_text": f"EMERGENCY ACTION COMPLETED: {res['message']} A security escalation ticket (#{res['ticket_id'][:8]}) has been dispatched to our fraud response unit.",
            }

        else:
            # Block card request
            card_type = "Credit Card" if "credit" in msg_lower else "Debit Card"
            res = block_card(db, customer_id, card_type=card_type, reason="Stolen / Lost / Fraud security block")
            if res["success"]:
                return {
                    "agent": "FraudAgent",
                    "tool_used": "block_card",
                    "result": res,
                    "response_text": f"{res['message']} Your card safety ticket ref is #{res['ticket_id'][:8]}.",
                }
            else:
                return {
                    "agent": "FraudAgent",
                    "tool_used": "block_card",
                    "result": res,
                    "response_text": f"Could not complete card block: {res.get('error')}. I am notifying security personnel.",
                }
