from lending_custom.loan_repayment_reconciliation import get_loan_repayments_for_bank_reconciliation

results = get_loan_repayments_for_bank_reconciliation('Loan Repayment Account (M-pesa) - CAL', from_date='2022-12-01')
print(f'Found {len(results)} loan repayments')
for r in results[:3]:
    print(f'{r["name"]}: {r["amount_paid"]}')