from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Customer
from app.agents.coordinator import CoordinatorAgent
from app.tools import auth_tools, banking_tools, loan_tools, fraud_tools, support_tools
from app.services.memory import MemoryManager
from app.services.logging import logger

vapi_router = APIRouter(prefix="/vapi", tags=["Vapi Integration"])


@vapi_router.post("/webhook")
async def vapi_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle incoming Vapi Webhook events (tool-calls, assistant-requests, status-updates)."""
    payload = await request.json()
    message_type = payload.get("message", {}).get("type") or payload.get("type")
    logger.info(f"[VAPI WEBHOOK] Received event type: {message_type}")

    # 1. Handle Vapi Tool Calls / Function Calls
    if message_type in ("tool-calls", "function-call"):
        call_info = payload.get("message", {}).get("call", {})
        call_id = call_info.get("id", "vapi-call-session")

        # Resolve session & customer context
        session = MemoryManager.get_or_create_session(db, call_id)
        default_customer = db.query(Customer).first()
        active_customer_id = session.customer_id or (default_customer.id if default_customer else None)

        # Extract function call details
        tool_calls = payload.get("message", {}).get("toolCalls", [])
        if not tool_calls and "functionCall" in payload.get("message", {}):
            tool_calls = [{"function": payload.get("message", {}).get("functionCall")}]

        results = []
        for tool_call in tool_calls:
            function_data = tool_call.get("function", {})
            func_name = function_data.get("name")
            args = function_data.get("arguments", {})

            if isinstance(args, str):
                import json

                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            logger.info(f"[VAPI TOOL CALL] Function: {func_name} | Args: {args} | Call ID: {call_id} | Active Customer: {active_customer_id}")

            # Use active customer ID if not provided in args
            target_customer_id = args.get("customer_id") or active_customer_id

            tool_result = {"error": f"Unknown function {func_name}"}

            if func_name == "verify_customer":
                tool_result = auth_tools.verify_customer(
                    db,
                    account_last_four=str(args.get("account_last_four", "")),
                    dob=str(args.get("dob", "")),
                    pin=str(args.get("pin", "")),
                    code_word=str(args.get("code_word", "")),
                    call_id=call_id,
                )
            elif func_name == "get_security_question":
                tool_result = auth_tools.get_security_question(
                    db,
                    account_last_four=str(args.get("account_last_four", "")),
                    dob=str(args.get("dob", "")),
                )
            elif func_name == "get_balance":
                tool_result = banking_tools.get_balance(db, customer_id=target_customer_id)
            elif func_name == "get_recent_transactions":
                tool_result = banking_tools.get_recent_transactions(
                    db, customer_id=target_customer_id, limit=args.get("limit", 5)
                )
            elif func_name == "get_account_details":
                tool_result = banking_tools.get_account_details(db, customer_id=target_customer_id)
            elif func_name == "block_card":
                tool_result = fraud_tools.block_card(
                    db,
                    customer_id=target_customer_id,
                    card_last_four=args.get("card_last_four"),
                    card_type=args.get("card_type", "Debit Card"),
                    reason=args.get("reason", "Lost card"),
                )
            elif func_name == "freeze_account":
                tool_result = fraud_tools.freeze_account(
                    db, customer_id=target_customer_id, reason=args.get("reason", "Fraud concern")
                )
            elif func_name == "check_loan_eligibility":
                tool_result = loan_tools.check_loan_eligibility(
                    db,
                    customer_id=target_customer_id,
                    requested_amount=float(args.get("requested_amount", 500000)),
                    loan_type=args.get("loan_type", "Home Loan"),
                )
            elif func_name == "calculate_emi":
                tool_result = loan_tools.calculate_emi(
                    principal=float(args.get("principal", 100000)),
                    annual_interest_rate=float(args.get("annual_interest_rate", 10.5)),
                    tenure_months=int(args.get("tenure_months", 36)),
                    db=db,
                    customer_id=target_customer_id,
                )
            elif func_name == "create_support_ticket":
                tool_result = support_tools.create_support_ticket(
                    db,
                    customer_id=target_customer_id,
                    issue_description=args.get("issue_description", "General query"),
                    category=args.get("category", "General"),
                )
            elif func_name == "transfer_to_human":
                tool_result = support_tools.transfer_to_human(
                    db, reason=args.get("reason", "Customer requested transfer"), call_id=call_id, customer_id=target_customer_id
                )

            results.append({"toolCallId": tool_call.get("id"), "result": str(tool_result)})

        return {"results": results}

    # 2. Handle Assistant Request (dynamic call greeting & context setup)
    elif message_type == "assistant-request":
        return {
            "assistant": {
                "firstMessage": "Welcome to Nexus Financial customer care. How may I assist you today?",
                "model": {
                    "provider": "custom-llm",
                    "url": "/api/agent/chat",
                },
            }
        }

    # 3. Default fallback acknowledgement
    return {"status": "success", "message": "Event processed successfully"}
