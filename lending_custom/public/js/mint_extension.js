// Extend Mint's MatchFilters component to include Loan Repayment and Loan Disbursement

// This script will be loaded after mint app loads to extend its functionality
(function() {
    'use strict';
    
    // Wait for mint app to load
    function waitForMintApp() {
        if (typeof window.React === 'undefined' || typeof window.frappe === 'undefined') {
            setTimeout(waitForMintApp, 100);
            return;
        }
        
        // Extend the match filters
        extendMintMatchFilters();
    }
    
    function extendMintMatchFilters() {
        // Hook into frappe's client-side API to ensure loan document types are included
        if (window.frappe && window.frappe.call) {
            const originalCall = window.frappe.call;
            
            window.frappe.call = function(opts) {
                // Intercept calls to get_linked_payments and ensure loan document types are included
                if (opts.method === 'erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.get_linked_payments') {
                    if (opts.args && opts.args.document_types) {
                        const docTypes = opts.args.document_types;
                        
                        // Add loan document types if they're not already included
                        if (!docTypes.includes('loan_repayment')) {
                            docTypes.push('loan_repayment');
                        }
                        if (!docTypes.includes('loan_disbursement')) {
                            docTypes.push('loan_disbursement');
                        }
                        
                        opts.args.document_types = docTypes;
                    }
                }
                
                return originalCall.call(this, opts);
            };
        }
        
        // Try to extend localStorage-based match filters for mint
        try {
            const storageKey = 'mint-bank-rec-match-filters';
            const existingFilters = JSON.parse(localStorage.getItem(storageKey) || '["payment_entry", "journal_entry"]');
            
            // Add loan document types if not already present
            const loanTypes = ['loan_repayment', 'loan_disbursement'];
            let updated = false;
            
            loanTypes.forEach(type => {
                if (!existingFilters.includes(type)) {
                    existingFilters.push(type);
                    updated = true;
                }
            });
            
            if (updated) {
                localStorage.setItem(storageKey, JSON.stringify(existingFilters));
                console.log('Extended mint bank reconciliation filters with loan document types');
            }
        } catch (e) {
            console.warn('Could not extend mint match filters:', e);
        }
    }
    
    // Start the extension process
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForMintApp);
    } else {
        waitForMintApp();
    }
})();