from lending.loan_management.doctype.loan_interest_accrual.loan_interest_accrual import get_term_loans
from frappe.utils import getdate

loans = get_term_loans(getdate('2022-03-31'))
print(f'Found {len(loans)} term loans')
if loans:
    for loan in loans[:3]:
        print(f'Loan: {loan.name}, Payment Date: {loan.payment_date}, Interest: {loan.interest_amount}, Accrued: {loan.is_accrued}')