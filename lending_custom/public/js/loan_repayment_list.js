// Loan Repayment List customizations
frappe.listview_settings['Loan Repayment'] = frappe.listview_settings['Loan Repayment'] || {};

// Add custom buttons to the list view
frappe.listview_settings['Loan Repayment'].onload = function(listview) {
    // Add button to check for missing GL entries
    listview.page.add_inner_button(__('Check Missing GL Entries'), function() {
        frappe.call({
            method: 'lending_custom.regenerate_gl_entries.preview_missing_gl_entries',
            freeze: true,
            freeze_message: __('Checking for Loan Repayments without GL entries...'),
            callback: function(r) {
                if (r.message) {
                    let data = r.message;
                    
                    if (data.total_count === 0) {
                        frappe.msgprint({
                            title: __('All Good!'),
                            indicator: 'green',
                            message: __('All Loan Repayments have GL entries.')
                        });
                        return;
                    }
                    
                    // Build the message with details
                    let msg = `
                        <div class="alert alert-warning">
                            <strong>${data.total_count}</strong> Loan Repayments are missing GL entries<br>
                            <strong>Total Amount:</strong> ${format_currency(data.total_amount)}
                        </div>
                        <p>Would you like to regenerate the GL entries for these repayments?</p>
                    `;
                    
                    frappe.confirm(
                        msg,
                        function() {
                            // User clicked Yes - regenerate GL entries
                            regenerate_gl_entries(data.total_count);
                        },
                        function() {
                            // User clicked No
                        }
                    );
                }
            }
        });
    }, __('Actions'));
    
    // Add button to regenerate GL entries directly
    listview.page.add_inner_button(__('Regenerate Missing GL Entries'), function() {
        frappe.prompt([
            {
                label: 'Limit (leave empty for all)',
                fieldname: 'limit',
                fieldtype: 'Int',
                description: 'Maximum number of repayments to process. Leave empty to process all.'
            }
        ],
        function(values) {
            regenerate_gl_entries(null, values.limit);
        },
        __('Regenerate GL Entries'),
        __('Regenerate')
        );
    }, __('Actions'));
};

function regenerate_gl_entries(expected_count, limit) {
    let msg = limit 
        ? __('Regenerating GL entries for up to {0} Loan Repayments...', [limit])
        : __('Regenerating GL entries for all Loan Repayments without them...');
    
    frappe.call({
        method: 'lending_custom.regenerate_gl_entries.regenerate_gl_entries_api',
        args: {
            limit: limit || null
        },
        freeze: true,
        freeze_message: msg,
        callback: function(r) {
            if (r.message) {
                let stats = r.message;
                
                let indicator = stats.errors > 0 ? 'orange' : 'green';
                let title = stats.errors > 0 ? __('Completed with Errors') : __('Success');
                
                frappe.msgprint({
                    title: title,
                    indicator: indicator,
                    message: `
                        <table class="table table-bordered">
                            <tr><td><strong>Total Processed</strong></td><td>${stats.processed}</td></tr>
                            <tr><td><strong>GL Entries Created</strong></td><td>${stats.success}</td></tr>
                            <tr><td><strong>Skipped</strong></td><td>${stats.skipped}</td></tr>
                            <tr><td><strong>Errors</strong></td><td>${stats.errors}</td></tr>
                            <tr><td><strong>Total Amount</strong></td><td>${format_currency(stats.total_amount)}</td></tr>
                        </table>
                    `
                });
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('An error occurred while regenerating GL entries. Please check the error log.')
            });
        }
    });
}
