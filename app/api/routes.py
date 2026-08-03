from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.tools import auth_tools, banking_tools, loan_tools, fraud_tools, support_tools
from app.agents.coordinator import CoordinatorAgent
from app.api.schemas import (
    VerifyUserRequest,
    VerifyUserResponse,
    AccountBalanceResponse,
    TransactionsResponse,
    AccountDetailsResponse,
    BlockCardRequest,
    BlockCardResponse,
    FreezeAccountRequest,
    FreezeAccountResponse,
    LoanEligibilityRequest,
    LoanEligibilityResponse,
    LoanRequestModel,
    LoanRequestResponse,
    SupportTicketRequest,
    SupportTicketResponse,
    TransferHumanRequest,
    TransferHumanResponse,
    AgentChatRequest,
    AgentChatResponse,
)

router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"], status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint for Docker & Cloud deployments (Railway / Render)."""
    return {"status": "healthy", "service": "AI Voice Banking Assistant", "version": "1.0.0"}



@router.get("/config")
def get_frontend_config():
    """Serve non-secret frontend config (public key + assistant ID) from env vars."""
    from app.config import settings
    return {
        "vapi_public_key": settings.VAPI_PUBLIC_KEY,
        "assistant_id": settings.VAPI_ASSISTANT_ID,
    }


@router.post("/verify-user", response_model=VerifyUserResponse)
def verify_user(payload: VerifyUserRequest, db: Session = Depends(get_db)):
    """Authenticate customer by account number last 4 digits and DOB."""
    res = auth_tools.verify_customer(
        db=db,
        account_last_four=payload.account_last_four,
        dob=payload.dob,
        pin=payload.pin,
        code_word=payload.code_word,
        call_id=payload.call_id,
    )
    return VerifyUserResponse(**res)


@router.get("/balance/{customer_id}", response_model=AccountBalanceResponse)
def get_balance(customer_id: str, db: Session = Depends(get_db)):
    """Fetch account balances for a customer."""
    res = banking_tools.get_balance(db, customer_id)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Customer not found"))
    return AccountBalanceResponse(**res)


@router.get("/transactions/{customer_id}", response_model=TransactionsResponse)
def get_transactions(customer_id: str, limit: int = 5, db: Session = Depends(get_db)):
    """Fetch recent transaction history for a customer."""
    res = banking_tools.get_recent_transactions(db, customer_id, limit=limit)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Customer not found"))
    return TransactionsResponse(**res)


@router.get("/account/{customer_id}", response_model=AccountDetailsResponse)
def get_account_details(customer_id: str, db: Session = Depends(get_db)):
    """Fetch customer account details."""
    res = banking_tools.get_account_details(db, customer_id)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Customer not found"))
    return AccountDetailsResponse(**res)


@router.post("/block-card", response_model=BlockCardResponse)
def block_card(payload: BlockCardRequest, db: Session = Depends(get_db)):
    """Block debit/credit card for security."""
    res = fraud_tools.block_card(
        db=db,
        customer_id=payload.customer_id,
        card_last_four=payload.card_last_four,
        card_type=payload.card_type,
        reason=payload.reason,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Card block failed"))
    return BlockCardResponse(**res)


@router.post("/freeze-account", response_model=FreezeAccountResponse)
def freeze_account(payload: FreezeAccountRequest, db: Session = Depends(get_db)):
    """Freeze all customer accounts."""
    res = fraud_tools.freeze_account(db=db, customer_id=payload.customer_id, reason=payload.reason)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Account freeze failed"))
    return FreezeAccountResponse(**res)


@router.post("/loan-eligibility", response_model=LoanEligibilityResponse)
def check_loan_eligibility(payload: LoanEligibilityRequest, db: Session = Depends(get_db)):
    """Check loan eligibility and calculate EMI capacity."""
    res = loan_tools.check_loan_eligibility(
        db=db,
        customer_id=payload.customer_id,
        requested_amount=payload.requested_amount,
        loan_type=payload.loan_type,
        monthly_income=payload.monthly_income,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Eligibility check failed"))
    return LoanEligibilityResponse(**res)


@router.post("/loan-request", response_model=LoanRequestResponse)
def create_loan_request(payload: LoanRequestModel, db: Session = Depends(get_db)):
    """Submit a formal loan inquiry application."""
    res = loan_tools.create_loan_request(
        db=db,
        customer_id=payload.customer_id,
        loan_type=payload.loan_type,
        amount=payload.amount,
        tenure_months=payload.tenure_months,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Loan request creation failed"))
    return LoanRequestResponse(**res)


@router.post("/support-ticket", response_model=SupportTicketResponse)
def create_support_ticket(payload: SupportTicketRequest, db: Session = Depends(get_db)):
    """Generate a support ticket."""
    res = support_tools.create_support_ticket(
        db=db,
        customer_id=payload.customer_id,
        issue_description=payload.issue_description,
        category=payload.category,
    )
    return SupportTicketResponse(**res)


@router.post("/transfer-human", response_model=TransferHumanResponse)
def transfer_human(payload: TransferHumanRequest, db: Session = Depends(get_db)):
    """Escalate call to a human operator."""
    res = support_tools.transfer_to_human(
        db=db,
        reason=payload.reason,
        call_id=payload.call_id,
        customer_id=payload.customer_id,
    )
    return TransferHumanResponse(**res)


@router.post("/agent/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest, db: Session = Depends(get_db)):
    """Interactive multi-agent chat endpoint simulating Vapi/Voice conversation turns."""
    res = CoordinatorAgent.process_call(db=db, call_id=payload.call_id, user_message=payload.message)
    return AgentChatResponse(**res)
