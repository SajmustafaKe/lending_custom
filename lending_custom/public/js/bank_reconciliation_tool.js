/**
 * Bank Reconciliation Tool Enhancement for Loan Repayments
 * 
 * This script adds an "Auto Reconcile Loans" button to the Bank Reconciliation Tool
 * that automatically reconciles Loan Repayments with Bank Transactions based on:
 * - Matching reference_number
 * - Matching amount (deposit == amount_paid)
 * - Matching date (bank transaction date == loan repayment posting_date)
 */

frappe.ui.form.on('Bank Reconciliation Tool', {
    refresh: function(frm) {
        // Add Auto Reconcile Loans button
        frm.add_custom_button(__('Auto Reconcile Loans'), function() {
            if (!frm.doc.bank_account) {
                frappe.msgprint(__('Please select a Bank Account first'));
                return;
            }
            
            frappe.confirm(
                __('This will automatically reconcile Bank Transactions with matching Loan Repayments. Do you want to continue?'),
                function() {
                    // Show progress
                    frappe.show_progress(__('Auto Reconciling Loans'), 0, 100, __('Processing...'));
                    
                    frappe.call({
                        method: 'lending_custom.loan_auto_reconciliation.auto_reconcile_loan_repayments',
                        args: {
                            bank_account: frm.doc.bank_account,
                            from_date: frm.doc.bank_statement_from_date,
                            to_date: frm.doc.bank_statement_to_date
                        },
                        callback: function(r) {
                            frappe.hide_progress();
                            
                            if (r.message) {
                                let result = r.message;
                                
                                // Show detailed results
                                let msg = `
                                    <div class="text-muted">
                                        <p><strong>Total Processed:</strong> ${result.total_processed}</p>
                                        <p><strong>Reconciled:</strong> <span class="text-success">${result.reconciled}</span></p>
                                        <p><strong>Skipped:</strong> ${result.skipped}</p>
                                        <p><strong>Failed:</strong> <span class="text-danger">${result.failed}</span></p>
                                    </div>
                                `;
                                
                                if (result.reconciled > 0) {
                                    frappe.msgprint({
                                        title: __('Auto Reconciliation Complete'),
                                        message: msg,
                                        indicator: 'green'
                                    });
                                    
                                    // Refresh the reconciliation tool
                                    frm.trigger('make_reconciliation_tool');
                                } else {
                                    frappe.msgprint({
                                        title: __('Auto Reconciliation Complete'),
                                        message: __('No matching Loan Repayments found for reconciliation.'),
                                        indicator: 'blue'
                                    });
                                }
                            }
                        },
                        error: function(r) {
                            frappe.hide_progress();
                            frappe.msgprint({
                                title: __('Error'),
                                message: __('An error occurred during auto reconciliation.'),
                                indicator: 'red'
                            });
                        }
                    });
                }
            );
        }, __('Actions'));
        
        // Add Preview Loan Matches button
        frm.add_custom_button(__('Preview Loan Matches'), function() {
            if (!frm.doc.bank_account) {
                frappe.msgprint(__('Please select a Bank Account first'));
                return;
            }
            
            frappe.call({
                method: 'lending_custom.loan_auto_reconciliation.get_loan_repayment_reconciliation_preview',
                args: {
                    bank_account: frm.doc.bank_account,
                    from_date: frm.doc.bank_statement_from_date,
                    to_date: frm.doc.bank_statement_to_date,
                    limit: 100
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        show_loan_matches_dialog(frm, r.message);
                    } else {
                        frappe.msgprint({
                            title: __('Preview Results'),
                            message: __('No matching Loan Repayments found.'),
                            indicator: 'blue'
                        });
                    }
                }
            });
        }, __('Actions'));
    }
});

/**
 * Show a dialog with loan matches that can be selected for reconciliation
 */
function show_loan_matches_dialog(frm, matches) {
    let fields = [
        {
            fieldtype: 'HTML',
            fieldname: 'matches_html'
        }
    ];
    
    let dialog = new frappe.ui.Dialog({
        title: __('Loan Repayment Matches ({0} found)', [matches.length]),
        fields: fields,
        size: 'extra-large',
        primary_action_label: __('Reconcile Selected'),
        primary_action: function() {
            let selected = [];
            dialog.$wrapper.find('input[data-bt-name]:checked').each(function() {
                selected.push($(this).data('bt-name'));
            });
            
            if (selected.length === 0) {
                frappe.msgprint(__('Please select at least one transaction to reconcile'));
                return;
            }
            
            dialog.hide();
            
            frappe.call({
                method: 'lending_custom.loan_auto_reconciliation.reconcile_selected_transactions',
                args: {
                    transactions: selected
                },
                callback: function(r) {
                    if (r.message) {
                        let reconciled = r.message.filter(x => x.status === 'reconciled').length;
                        frappe.msgprint({
                            title: __('Reconciliation Complete'),
                            message: __('Successfully reconciled {0} transaction(s)', [reconciled]),
                            indicator: 'green'
                        });
                        
                        // Refresh the reconciliation tool
                        frm.trigger('make_reconciliation_tool');
                    }
                }
            });
        }
    });
    
    // Build HTML table
    let html = `
        <div class="loan-matches-container">
            <div class="mb-3">
                <button class="btn btn-xs btn-default" onclick="toggle_all_matches(true)">Select All</button>
                <button class="btn btn-xs btn-default" onclick="toggle_all_matches(false)">Deselect All</button>
            </div>
            <table class="table table-bordered table-hover">
                <thead>
                    <tr>
                        <th style="width: 30px;"><input type="checkbox" id="select-all-matches" onclick="toggle_all_matches(this.checked)"></th>
                        <th>Bank Transaction</th>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Reference</th>
                        <th>Loan Repayment</th>
                        <th>Loan</th>
                        <th>Applicant</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    matches.forEach(function(match) {
        html += `
            <tr>
                <td><input type="checkbox" data-bt-name="${match.bank_transaction}" checked></td>
                <td><a href="/app/bank-transaction/${match.bank_transaction}" target="_blank">${match.bank_transaction}</a></td>
                <td>${frappe.datetime.str_to_user(match.bank_transaction_date)}</td>
                <td class="text-right">${format_currency(match.bank_transaction_amount)}</td>
                <td>${match.bank_transaction_reference || ''}</td>
                <td><a href="/app/loan-repayment/${match.loan_repayment}" target="_blank">${match.loan_repayment}</a></td>
                <td><a href="/app/loan/${match.loan}" target="_blank">${match.loan}</a></td>
                <td>${match.applicant || ''}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        <style>
            .loan-matches-container {
                max-height: 400px;
                overflow-y: auto;
            }
            .loan-matches-container table {
                font-size: 12px;
            }
        </style>
    `;
    
    dialog.fields_dict.matches_html.$wrapper.html(html);
    dialog.show();
}

/**
 * Toggle all checkboxes in the matches dialog
 */
window.toggle_all_matches = function(checked) {
    $('input[data-bt-name]').prop('checked', checked);
    $('#select-all-matches').prop('checked', checked);
};
