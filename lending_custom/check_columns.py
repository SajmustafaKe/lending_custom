import frappe

def execute():
	# Check if custom field exists
	cf = frappe.get_all('Custom Field', filters={'dt': 'Loan Application', 'fieldname': 'interest_calculation_method'}, fields=['name', 'dt', 'fieldname', 'fieldtype', 'options', 'disabled'])
	print(f"Custom Field for Loan Application: {cf}")

	cf_loan_product = frappe.get_all('Custom Field', filters={'dt': 'Loan Product', 'fieldname': 'interest_calculation_method'}, fields=['name', 'dt', 'fieldname', 'fieldtype', 'options', 'disabled'])
	print(f"Custom Field for Loan Product: {cf_loan_product}")

	# Check columns in Loan Application table
	try:
		columns = frappe.db.sql("DESCRIBE `tabLoan Application`", as_dict=True)
		column_names = [col['Field'] for col in columns]
		print(f"Columns in tabLoan Application: {'interest_calculation_method' in column_names}")
	except Exception as e:
		print(f"Error: {e}")