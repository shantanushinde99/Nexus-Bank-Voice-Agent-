import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Get API key from env or script fallback
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
SERVER_URL = "https://rental-hardy-exerciser.ngrok-free.dev/api/vapi/webhook"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}

TWO_TOOLS = [
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
]


def register_two_tools():
    """Register verify_customer and get_balance custom tools."""
    print(f"Registering verify_customer and get_balance with SERVER_URL: {SERVER_URL}...")
    for tool in TWO_TOOLS:
        tool_name = tool["function"]["name"]
        try:
            resp = httpx.post("https://api.vapi.ai/tool", headers=headers, json=tool, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                print(f"[SUCCESS] Registered Tool '{tool_name}' -> ID: {data.get('id')}")
            else:
                print(f"[INFO] Response for '{tool_name}': {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    register_two_tools()
