from lending.loan_management.doctype.loan_interest_accrual.loan_interest_accrual import make_accrual_interest_entry_for_term_loans
from frappe.utils import getdate, add_days
import frappe

process_id = 'LM-PLA-00072'
start_date = getdate('2022-03-01')
end_date = getdate('2022-03-01')  # Only one date

current_date = start_date
while current_date <= end_date:
    print(f"Processing for {current_date}")
    try:
        make_accrual_interest_entry_for_term_loans(
            posting_date=current_date,
            process_loan_interest=process_id,
            accrual_type="Regular"
        )
        print(f"Success for {current_date}")
    except Exception as e:
        print(f"Error for {current_date}: {e}")
    current_date = add_days(current_date, 1)

print("Done")