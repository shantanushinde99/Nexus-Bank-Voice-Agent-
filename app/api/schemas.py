from pydantic import BaseModel, Field
from typing import Optional, List


class VerifyUserRequest(BaseModel):
    account_last_four: str = Field(..., json_schema_extra={"example": "4567"})
    dob: str = Field(..., json_schema_extra={"example": "1999-08-14"})
    call_id: Optional[str] = Field(default="demo-call-101")


class VerifyUserResponse(BaseModel):
    success: bool
    message: str
    customer_id: Optional[str] = None
    full_name: Optional[str] = None
    failed_attempts: int = 0
    should_escalate: bool = False


class AccountBalanceResponse(BaseModel):
    success: bool
    customer_name: Optional[str] = None
    accounts: List[dict] = []
    total_balance: float = 0.0
    formatted_total_balance: str = "₹0.00"
    error: Optional[str] = None


class TransactionsResponse(BaseModel):
    success: bool
    customer_name: Optional[str] = None
    transactions: List[dict] = []
    count: int = 0
    error: Optional[str] = None


class AccountDetailsResponse(BaseModel):
    success: bool
    customer_id: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    dob: Optional[str] = None
    accounts: List[dict] = []
    error: Optional[str] = None


class BlockCardRequest(BaseModel):
    customer_id: str
    card_last_four: Optional[str] = None
    card_type: str = "Debit Card"
    reason: str = "Card lost or stolen"


class BlockCardResponse(BaseModel):
    success: bool
    customer_name: Optional[str] = None
    blocked_cards: List[dict] = []
    message: str
    ticket_id: Optional[str] = None
    error: Optional[str] = None


class FreezeAccountRequest(BaseModel):
    customer_id: str
    reason: str = "Account fraud threat"


class FreezeAccountResponse(BaseModel):
    success: bool
    customer_name: Optional[str] = None
    frozen_accounts: List[str] = []
    message: str
    ticket_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class LoanEligibilityRequest(BaseModel):
    customer_id: str
    requested_amount: float = Field(..., json_schema_extra={"example": 500000.0})
    loan_type: str = Field(default="Personal Loan", json_schema_extra={"example": "Personal Loan"})
    monthly_income: float = Field(default=65000.0, json_schema_extra={"example": 65000.0})


class LoanEligibilityResponse(BaseModel):
    success: bool
    is_eligible: bool = False
    customer_name: Optional[str] = None
    loan_type: str = ""
    requested_amount: float = 0.0
    formatted_requested_amount: str = "₹0.00"
    max_eligible_amount: float = 0.0
    formatted_max_eligible_amount: str = "₹0.00"
    estimated_monthly_emi: float = 0.0
    formatted_estimated_emi: str = "₹0.00"
    interest_rate: float = 0.0
    tenure_months: int = 36
    rejection_reason: Optional[str] = None
    error: Optional[str] = None


class LoanRequestModel(BaseModel):
    customer_id: str
    loan_type: str = "Personal Loan"
    amount: float = 300000.0
    tenure_months: int = 36


class LoanRequestResponse(BaseModel):
    success: bool
    loan_id: Optional[str] = None
    customer_name: Optional[str] = None
    loan_type: Optional[str] = None
    amount: float = 0.0
    formatted_amount: str = "₹0.00"
    emi: float = 0.0
    formatted_emi: str = "₹0.00"
    status: Optional[str] = None
    message: str
    error: Optional[str] = None


class SupportTicketRequest(BaseModel):
    customer_id: Optional[str] = None
    issue_description: str
    category: str = "General Support"


class SupportTicketResponse(BaseModel):
    success: bool
    ticket_id: Optional[str] = None
    issue: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    message: str


class TransferHumanRequest(BaseModel):
    session_id: Optional[str] = None
    call_id: Optional[str] = None
    customer_id: Optional[str] = None
    reason: str = "Customer requested human support"


class TransferHumanResponse(BaseModel):
    success: bool
    transfer: bool = True
    destination: str
    reason: str
    ticket_id: Optional[str] = None
    message: str


class AgentChatRequest(BaseModel):
    call_id: str = Field(default="demo-call-101", json_schema_extra={"example": "demo-call-101"})
    message: str = Field(..., json_schema_extra={"example": "What is my account balance?"})


class AgentChatResponse(BaseModel):
    session_id: str
    authenticated: bool
    customer_id: Optional[str] = None
    agent: str
    tool_used: Optional[str] = None
    transfer_human: bool = False
    auth_prompt: bool = False
    response_text: str
