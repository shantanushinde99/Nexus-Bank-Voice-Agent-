# Product Context: AI Voice Banking Assistant

## Why This Project Exists
Modern financial institutions require automated yet empathetic and highly secure customer interaction channels. This AI Voice Banking Assistant showcases an end-to-end voice architecture operating with strict security controls, multi-agent specialization, and real-time backend tool interaction.

## Core User Workflows
1. **Authentication Flow**:
   - Customer calls in → System asks for last 4 digits of account number + DOB.
   - Authentication agent verifies using `verify_customer()` tool.
   - On success, session marked as `authenticated=True`.
   - On failure (3 consecutive times), auto-escalates to human agent.

2. **Banking Services Flow**:
   - Check account balance (`get_balance`).
   - Retrieve recent transactions (`get_recent_transactions`).
   - Get full account details (`get_account_details`).

3. **Loan Assistance Flow**:
   - Check loan eligibility (`check_loan_eligibility`).
   - Calculate EMI based on principal, rate, tenure (`calculate_emi`).
   - Submit formal loan inquiries (`create_loan_request`).

4. **Fraud & Emergency Handling Flow**:
   - Block lost/stolen debit or credit cards (`block_card`).
   - Freeze full bank account (`freeze_account`).
   - Raise urgent security ticket (`create_support_ticket`).

5. **Support & Escalation Flow**:
   - Answer general queries.
   - Create generic support tickets (`create_support_ticket`).
   - Transfer to human operator (`transfer_to_human`).

## User Experience Goals
- Natural conversational flow with dynamic context preservation (e.g. "What about my last transaction?" refers to authenticated customer).
- Zero leaks of sensitive data prior to authentication.
- Real-time audit trail for all operational actions.
