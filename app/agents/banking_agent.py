from sqlalchemy.orm import Session
from app.tools.banking_tools import get_balance, get_recent_transactions, get_account_details


class BankingAgent:
    """Specialized Agent for Account Balances and Transactions."""

    @staticmethod
    def process_request(db: Session, customer_id: str, intent: str, user_message: str) -> dict:
        if "balance" in intent or "balance" in user_message.lower():
            res = get_balance(db, customer_id)
            if not res["success"]:
                return {"agent": "BankingAgent", "response_text": "Could not retrieve account balance."}

            accounts_summary = ", ".join([f"{acc.get('account_type', 'Account')} (ending {acc.get('account_number', '')}): {acc.get('formatted_balance', '₹0.00')}" for acc in res.get("accounts", [])])
            return {
                "agent": "BankingAgent",
                "tool_used": "get_balance",
                "result": res,
                "response_text": f"Your total account balance is {res.get('formatted_total_balance', '₹0.00')}. Breakdown: {accounts_summary}. Would you also like to hear your recent transactions?",
            }

        elif "transaction" in intent or "history" in user_message.lower() or "transaction" in user_message.lower() or "recent" in user_message.lower():
            res = get_recent_transactions(db, customer_id, limit=5)
            if not res["success"]:
                return {"agent": "BankingAgent", "response_text": "Could not retrieve recent transactions."}

            if not res["transactions"]:
                return {"agent": "BankingAgent", "response_text": "You have no recent transactions on your account."}

            tx_lines = [
                f"{tx['type']} of {tx['formatted_amount']} at {tx['merchant']} on {tx['timestamp']}"
                for tx in res["transactions"]
            ]
            summary = "; ".join(tx_lines)
            return {
                "agent": "BankingAgent",
                "tool_used": "get_recent_transactions",
                "result": res,
                "response_text": f"Here are your last {len(res['transactions'])} transactions: {summary}.",
            }

        else:
            res = get_account_details(db, customer_id)
            if not res["success"]:
                return {"agent": "BankingAgent", "response_text": "Could not retrieve account details."}
            return {
                "agent": "BankingAgent",
                "tool_used": "get_account_details",
                "result": res,
                "response_text": f"Account profile for {res['full_name']} (Phone: {res['phone_number']}): {len(res['accounts'])} active account(s) registered.",
            }
