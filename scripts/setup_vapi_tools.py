import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
SERVER_URL = "https://rental-hardy-exerciser.ngrok-free.dev/api/vapi/webhook"

if not VAPI_API_KEY:
    print("Error: VAPI_API_KEY is missing in .env file.")
    exit(1)

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}

TOOLS = [
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "verify_customer",
            "description": "Verify customer identity by last 4 digits of account number and date of birth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_last_four": {"type": "string", "description": "Last 4 digits of account number"},
                    "dob": {"type": "string", "description": "Date of birth (YYYY-MM-DD or DD Month YYYY)"},
                },
                "required": ["account_last_four", "dob"],
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Fetch account balances for the customer in INR.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "get_recent_transactions",
            "description": "Fetch recent transaction history for customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "limit": {"type": "integer", "description": "Number of transactions to fetch"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "get_account_details",
            "description": "Retrieve customer account profile and details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "block_card",
            "description": "Block lost or stolen debit or credit card.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "card_last_four": {"type": "string", "description": "Last 4 digits of card"},
                    "card_type": {"type": "string", "description": "Debit Card or Credit Card"},
                    "reason": {"type": "string", "description": "Reason for block"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "freeze_account",
            "description": "Freeze all bank accounts for customer security.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "reason": {"type": "string", "description": "Reason for freeze"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "check_loan_eligibility",
            "description": "Check customer eligibility for home, auto, or personal loan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "requested_amount": {"type": "number", "description": "Requested loan amount in INR"},
                    "loan_type": {"type": "string", "description": "Loan type (Personal Loan, Home Loan, Auto Loan)"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "calculate_emi",
            "description": "Calculate monthly loan EMI and total interest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {"type": "number", "description": "Loan amount"},
                    "annual_interest_rate": {"type": "number", "description": "Annual interest rate percentage"},
                    "tenure_months": {"type": "integer", "description": "Tenure in months"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "create_loan_request",
            "description": "Submit formal loan application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "loan_type": {"type": "string", "description": "Loan type"},
                    "amount": {"type": "number", "description": "Loan amount"},
                    "tenure_months": {"type": "integer", "description": "Tenure in months"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Generate a customer support ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "issue_description": {"type": "string", "description": "Issue details"},
                    "category": {"type": "string", "description": "Inquiry category"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "async": False,
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "Escalate call to a human operator.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for human transfer"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
]


def register_vapi_tools():
    """Register all 11 tools with Vapi REST API automatically."""
    created_tool_ids = []
    print(f"Registering {len(TOOLS)} custom tools with Vapi API...")

    for tool in TOOLS:
        tool_name = tool["function"]["name"]
        try:
            resp = httpx.post("https://api.vapi.ai/tool", headers=headers, json=tool, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                tool_id = data.get("id")
                created_tool_ids.append(tool_id)
                print(f"[SUCCESS] Created Tool: '{tool_name}' (ID: {tool_id})")
            else:
                print(f"[WARNING] Failed to create '{tool_name}': {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[ERROR] Error creating '{tool_name}': {e}")

    print(f"\nSuccessfully created {len(created_tool_ids)} / {len(TOOLS)} tools in Vapi!")
    return created_tool_ids


if __name__ == "__main__":
    register_vapi_tools()
