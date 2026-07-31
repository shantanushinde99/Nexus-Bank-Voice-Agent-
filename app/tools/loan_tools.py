import math
from sqlalchemy.orm import Session
from app.database.models import Customer, Account, Loan
from app.services.audit import log_audit_event
from app.services.currency import format_inr_spoken, format_inr_display


def calculate_emi(
    principal: float,
    annual_interest_rate: float,
    tenure_months: int,
    db: Session | None = None,
    customer_id: str | None = None,
) -> dict:
    """Calculate Equated Monthly Installment (EMI) using financial math."""
    if principal <= 0 or annual_interest_rate <= 0 or tenure_months <= 0:
        return {
            "success": False,
            "error": "Invalid loan parameters provided.",
            "monthly_emi": 0.0,
            "formatted_monthly_emi": "₹0.00",
        }

    monthly_rate = (annual_interest_rate / 100) / 12
    # Formula: P * r * (1+r)^n / ((1+r)^n - 1)
    emi = (principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months)) / (
        math.pow(1 + monthly_rate, tenure_months) - 1
    )
    total_payment = emi * tenure_months
    total_interest = total_payment - principal

    if db:
        log_audit_event(
            db,
            tool_called="calculate_emi",
            status="SUCCESS",
            customer_id=customer_id,
            details=f"Principal: ₹{principal:,.2f}, Rate: {annual_interest_rate}%, Tenure: {tenure_months}m -> EMI: ₹{emi:,.2f}",
        )

    return {
        "success": True,
        "principal": principal,
        "display_principal": format_inr_display(principal),
        "spoken_principal": format_inr_spoken(principal),
        "annual_interest_rate": annual_interest_rate,
        "tenure_months": tenure_months,
        "monthly_emi": round(emi, 2),
        "display_monthly_emi": format_inr_display(round(emi, 2)),
        "spoken_monthly_emi": format_inr_spoken(round(emi, 2)),
        "total_interest_payable": round(total_interest, 2),
        "display_total_interest": format_inr_display(round(total_interest, 2)),
        "spoken_total_interest": format_inr_spoken(round(total_interest, 2)),
        "total_payment": round(total_payment, 2),
        "display_total_payment": format_inr_display(round(total_payment, 2)),
        "spoken_total_payment": format_inr_spoken(round(total_payment, 2)),
    }


def check_loan_eligibility(
    db: Session,
    customer_id: str,
    requested_amount: float = 0.0,
    loan_type: str = "Personal Loan",
    monthly_income: float = 65000.0,
) -> dict:
    """Check customer eligibility for a new loan based on income, balance, and existing debt."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        log_audit_event(db, "check_loan_eligibility", "FAILED", customer_id, "Customer not found")
        return {"success": False, "error": "Customer not found"}

    accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
    total_balance = sum(acc.balance for acc in accounts)

    existing_loans = db.query(Loan).filter(Loan.customer_id == customer_id, Loan.status == "Active").all()
    existing_emis = sum(l.emi for l in existing_loans)

    # Max allowed total monthly EMI is 50% of monthly income
    max_allowed_emi = monthly_income * 0.50
    available_emi_capacity = max(0.0, max_allowed_emi - existing_emis)

    # Standard interest rate by loan type
    interest_rates = {
        "Home Loan": 8.5,
        "Personal Loan": 11.5,
        "Auto Loan": 9.25,
        "Education Loan": 8.75,
    }
    rate = interest_rates.get(loan_type, 11.0)
    tenure_months = 60 if loan_type != "Home Loan" else 240

    max_eligible_loan = (
        available_emi_capacity
        * (math.pow(1 + (rate / 1200), tenure_months) - 1)
        / ((rate / 1200) * math.pow(1 + (rate / 1200), tenure_months))
    )

    # Default to max_eligible_loan if requested_amount <= 0
    if requested_amount <= 0:
        requested_amount = round(max_eligible_loan, 2)

    emi_calc = calculate_emi(requested_amount, rate, tenure_months)
    monthly_emi = emi_calc.get("monthly_emi", 0.0)
    formatted_monthly_emi = emi_calc.get("formatted_monthly_emi", f"₹{monthly_emi:,.2f}")

    is_eligible = False
    rejection_reason = None

    if available_emi_capacity <= 0:
        rejection_reason = "Existing loan EMIs exceed allowable monthly debt-to-income ratio (50%)."
    elif monthly_emi > available_emi_capacity:
        rejection_reason = f"Requested EMI of {formatted_monthly_emi} exceeds available EMI capacity of ₹{available_emi_capacity:,.2f}. Max eligible loan is ₹{round(max_eligible_loan, 2):,.2f}."
    else:
        is_eligible = True

    log_audit_event(
        db,
        tool_called="check_loan_eligibility",
        status="SUCCESS" if is_eligible else "DENIED",
        customer_id=customer_id,
        details=f"Eligible: {is_eligible} for ₹{requested_amount:,.2f} {loan_type}",
    )

    return {
        "success": True,
        "is_eligible": is_eligible,
        "customer_name": customer.full_name,
        "loan_type": loan_type,
        "requested_amount": requested_amount,
        "display_requested_amount": format_inr_display(requested_amount),
        "spoken_requested_amount": format_inr_spoken(requested_amount),
        "max_eligible_amount": round(max_eligible_loan, 2),
        "display_max_eligible_amount": format_inr_display(round(max_eligible_loan, 2)),
        "spoken_max_eligible_amount": format_inr_spoken(round(max_eligible_loan, 2)),
        "estimated_monthly_emi": monthly_emi,
        "display_estimated_emi": format_inr_display(monthly_emi),
        "spoken_estimated_emi": format_inr_spoken(monthly_emi),
        "interest_rate": rate,
        "tenure_months": tenure_months,
        "rejection_reason": rejection_reason,
    }


def create_loan_request(
    db: Session,
    customer_id: str,
    loan_type: str,
    amount: float,
    tenure_months: int = 36,
) -> dict:
    """Submit a loan application on behalf of the customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        log_audit_event(db, "create_loan_request", "FAILED", customer_id, "Customer not found")
        return {"success": False, "error": "Customer not found"}

    rates = {"Home Loan": 8.5, "Personal Loan": 11.5, "Auto Loan": 9.25, "Education Loan": 8.75}
    rate = rates.get(loan_type, 11.0)
    emi_data = calculate_emi(amount, rate, tenure_months)

    new_loan = Loan(
        customer_id=customer_id,
        loan_type=loan_type,
        amount=amount,
        emi=emi_data.get("monthly_emi", 0.0),
        interest_rate=rate,
        status="Applied",
    )
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)

    log_audit_event(
        db,
        tool_called="create_loan_request",
        status="SUCCESS",
        customer_id=customer_id,
        details=f"Created loan application ID {new_loan.id}: ₹{amount:,.2f} ({loan_type})",
    )

    return {
        "success": True,
        "loan_id": new_loan.id,
        "customer_name": customer.full_name,
        "loan_type": loan_type,
        "amount": amount,
        "display_amount": format_inr_display(amount),
        "spoken_amount": format_inr_spoken(amount),
        "emi": emi_data.get("monthly_emi", 0.0),
        "display_emi": emi_data.get("display_monthly_emi", format_inr_display(emi_data.get('monthly_emi', 0.0))),
        "spoken_emi": emi_data.get("spoken_monthly_emi", format_inr_spoken(emi_data.get('monthly_emi', 0.0))),
        "status": "Applied",
        "message": f"Your application for a {loan_type} of {format_inr_spoken(amount)} has been submitted successfully.",
    }
