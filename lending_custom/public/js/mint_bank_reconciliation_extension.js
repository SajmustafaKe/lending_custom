frappe.provide('mint.bankReconciliation');

// Extend mint's bank reconciliation match filters to include loan document types
$(document).ready(function() {
    if (window.mint && window.mint.bankReconciliation) {
        // Add loan document types to the available filters
        const originalMatchFilters = window.mint.bankReconciliation.matchFilters || [];
        
        // Ensure loan document types are included
        const loanDocTypes = ['loan_repayment', 'loan_disbursement'];
        loanDocTypes.forEach(docType => {
            if (!originalMatchFilters.includes(docType)) {
                originalMatchFilters.push(docType);
            }
        });
        
        window.mint.bankReconciliation.matchFilters = originalMatchFilters;
    }
});

// Override the mint match filters component if available
if (typeof window.mintMatchFilters !== 'undefined') {
    const originalMatchFilters = window.mintMatchFilters;
    
    window.mintMatchFilters = function(options) {
        // Add loan document types to options
        if (options && options.documentTypes) {
            const loanDocTypes = ['loan_repayment', 'loan_disbursement'];
            loanDocTypes.forEach(docType => {
                if (!options.documentTypes.includes(docType)) {
                    options.documentTypes.push(docType);
                }
            });
        }
        
        return originalMatchFilters(options);
    };
}