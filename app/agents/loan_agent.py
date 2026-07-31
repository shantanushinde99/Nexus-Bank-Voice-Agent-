import re
from sqlalchemy.orm import Session
from app.tools.loan_tools import check_loan_eligibility, calculate_emi, create_loan_request


class LoanAgent:
    """Specialized Agent for Loans and EMI Calculations."""

    @staticmethod
    def process_request(db: Session, customer_id: str, intent: str, user_message: str) -> dict:
        msg_lower = user_message.lower()

        # Parse potential amounts from message (e.g. 500000 or 5 lakhs)
        amount = 500000.0
        amount_match = re.search(r"(\d+[\d,.]*)", user_message)
        if amount_match:
            try:
                raw_num = amount_match.group(1).replace(",", "")
                amount = float(raw_num)
                if amount < 100:  # Handle "5 lakhs"
                    amount *= 100000
            except ValueError:
                pass

        if "emi" in intent or "calculate" in msg_lower or "emi" in msg_lower:
            rate = 10.5
            tenure = 36
            res = calculate_emi(amount, rate, tenure, db=db, customer_id=customer_id)
            return {
                "agent": "LoanAgent",
                "tool_used": "calculate_emi",
                "result": res,
                "response_text": f"For a loan amount of {res['formatted_principal']} at {rate}% annual interest for {tenure} months, your estimated monthly EMI will be {res['formatted_monthly_emi']}. Total interest payable is {res['formatted_total_interest']}.",
            }

        elif "apply" in intent or "request" in msg_lower or "create" in msg_lower:
            loan_type = "Personal Loan"
            if "home" in msg_lower:
                loan_type = "Home Loan"
            elif "auto" in msg_lower or "car" in msg_lower:
                loan_type = "Auto Loan"

            res = create_loan_request(db, customer_id, loan_type, amount, tenure_months=36)
            return {
                "agent": "LoanAgent",
                "tool_used": "create_loan_request",
                "result": res,
                "response_text": res["message"],
            }

        else:
            # Default to checking eligibility
            loan_type = "Personal Loan"
            if "home" in msg_lower:
                loan_type = "Home Loan"
            elif "auto" in msg_lower or "car" in msg_lower:
                loan_type = "Auto Loan"

            res = check_loan_eligibility(db, customer_id, requested_amount=amount, loan_type=loan_type)
            if res["is_eligible"]:
                return {
                    "agent": "LoanAgent",
                    "tool_used": "check_loan_eligibility",
                    "result": res,
                    "response_text": f"Great news! You are eligible for a {loan_type} up to {res['formatted_max_eligible_amount']}. Your estimated monthly EMI for {res['formatted_requested_amount']} will be {res['formatted_estimated_emi']}. Would you like me to submit an application for you?",
                }
            else:
                return {
                    "agent": "LoanAgent",
                    "tool_used": "check_loan_eligibility",
                    "result": res,
                    "response_text": f"Based on your current account profile, you are not eligible for {res['formatted_requested_amount']}. Reason: {res['rejection_reason']}",
                }
