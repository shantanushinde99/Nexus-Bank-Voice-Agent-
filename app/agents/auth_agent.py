from sqlalchemy.orm import Session
from app.tools.auth_tools import verify_customer
from app.tools.support_tools import transfer_to_human


class AuthAgent:
    """Specialized Authentication Agent."""

    @staticmethod
    def handle_auth(
        db: Session,
        account_last_four: str,
        dob: str,
        call_id: str,
    ) -> dict:
        result = verify_customer(db, account_last_four, dob, call_id)

        if result["success"]:
            return {
                "agent": "AuthAgent",
                "success": True,
                "customer_id": result["customer_id"],
                "full_name": result["full_name"],
                "response_text": f"Authentication successful. Welcome, {result['full_name']}! How can I assist you with your account today?",
            }

        if result.get("should_escalate"):
            transfer_res = transfer_to_human(
                db,
                reason="Authentication failed 3 consecutive times",
                call_id=call_id,
            )
            return {
                "agent": "AuthAgent",
                "success": False,
                "customer_id": None,
                "escalated": True,
                "response_text": "I'm sorry, but authentication failed three times. For security reasons, I am escalating your call to a human representative.",
                "transfer_details": transfer_res,
            }

        remaining = 3 - result.get("failed_attempts", 1)
        return {
            "agent": "AuthAgent",
            "success": False,
            "customer_id": None,
            "escalated": False,
            "response_text": f"Verification failed. The account number or date of birth provided did not match. Please try again. (Attempts remaining: {remaining})",
        }
