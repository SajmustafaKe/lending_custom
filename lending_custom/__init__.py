__version__ = "0.0.1"

# Apply lending overrides when the module is imported
def _apply_overrides():
	"""Apply overrides when module is loaded"""
	try:
		# Only import and apply if not already applied
		import frappe
		if hasattr(frappe, '_lending_overrides_applied'):
			return
			
		from lending_custom.function_overrides import apply_lending_overrides
		apply_lending_overrides()
		
		# Mark as applied to avoid duplicate applications
		frappe._lending_overrides_applied = True
		
	except Exception:
		# Silently fail during import - overrides will be applied later via patches
		pass

# Apply overrides
_apply_overrides()
