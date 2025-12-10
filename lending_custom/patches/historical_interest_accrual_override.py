import frappe

def execute():
	"""
	Patch to enable historical processing of loan interest accrual by overriding the get_term_loans function.
	This removes the restriction that loan schedules must be "Active" to allow processing of closed loans.
	"""
	try:
		from lending_custom.function_overrides import apply_lending_overrides
		
		# Apply the override
		apply_lending_overrides()
		
		frappe.db.commit()
		print("✅ Successfully applied get_term_loans override for historical interest accrual processing")
		
	except Exception as e:
		frappe.log_error(f"Error in patch: {str(e)}")
		print(f"❌ Error applying override: {str(e)}")
		raise