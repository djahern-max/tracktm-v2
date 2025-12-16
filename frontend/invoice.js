// Invoice Generation Module
// Handles invoice modal, form validation, and PDF generation

// Use API_BASE from app.js (no declaration needed - it's already on window)
// Just access window.API_BASE directly throughout this file

// Immediately export module to window object FIRST
window.InvoiceModule = window.InvoiceModule || {};

// Load saved invoice settings from localStorage
function loadInvoiceSettings() {
    return {
        ship_to: localStorage.getItem('inv_ship_to') || 'Newport, RI',
        billto_name: localStorage.getItem('inv_billto_name') || 'Reagan Marine Construction LLC',
        billto_address1: localStorage.getItem('inv_billto_address1') || '221 Third St, 5th Floor Suite 513',
        billto_address2: localStorage.getItem('inv_billto_address2') || 'Newport, RI 02840',
        contract_number: localStorage.getItem('inv_contract_number') || '',
        payment_terms: localStorage.getItem('inv_payment_terms') || '30',
        aggregation_method: localStorage.getItem('inv_aggregation_method') || 'category'
    };
}

// Save invoice settings to localStorage
function saveInvoiceSettings(data) {
    localStorage.setItem('inv_ship_to', data.ship_to);
    localStorage.setItem('inv_billto_name', data.billto_name);
    localStorage.setItem('inv_billto_address1', data.billto_address1);
    localStorage.setItem('inv_billto_address2', data.billto_address2);
    localStorage.setItem('inv_contract_number', data.contract_number);
    localStorage.setItem('inv_payment_terms', data.payment_terms);
    localStorage.setItem('inv_aggregation_method', data.aggregation_method);
}

// Open invoice modal and populate with saved/current values
async function openInvoiceModal() {
    const jobNumber = document.getElementById('jobNumber').value;
    const jobName = document.getElementById('jobName').value;

    if (!jobNumber) {
        alert('Please enter job number');
        return;
    }

    // Load saved settings
    const settings = loadInvoiceSettings();

    // Try to fetch job-specific defaults from API
    let jobDefaults = {};
    try {
        const response = await fetch(`${window.API_BASE}/job-invoice-defaults/${jobNumber}`);
        if (response.ok) {
            const data = await response.json();
            jobDefaults = data.defaults || {};
        }
    } catch (error) {
        console.log('No job-specific defaults found, using saved settings');
    }

    // Populate form - priority: job defaults > saved settings > empty
    document.getElementById('inv_job_number').value = jobNumber;
    document.getElementById('inv_job_name').value = jobDefaults.job_name || jobName || `Job ${jobNumber}`;
    document.getElementById('inv_invoice_number').value = '';
    document.getElementById('inv_purchase_order').value = '';
    document.getElementById('inv_payment_terms').value = settings.payment_terms;
    document.getElementById('inv_aggregation_method').value = settings.aggregation_method;

    // Ship to and contract - use job defaults if available
    document.getElementById('inv_ship_to').value = jobDefaults.ship_to_location || settings.ship_to;
    document.getElementById('inv_contract_number').value = jobDefaults.contract_number || settings.contract_number;

    // Company info (Remit To) - Always TSI defaults
    document.getElementById('inv_company_name').value = 'Tri-State Painting, LLC (TSI)';
    document.getElementById('inv_company_address1').value = '612 West Main Street Unit 2';
    document.getElementById('inv_company_address2').value = 'Tilton, NH 03276';
    document.getElementById('inv_company_phone').value = '(603) 286-7657';
    document.getElementById('inv_company_fax').value = '(603) 286-7882';

    // Bill to info - use job defaults if available, otherwise saved settings
    document.getElementById('inv_billto_name').value = jobDefaults.bill_to_name || settings.billto_name;
    document.getElementById('inv_billto_address1').value = jobDefaults.bill_to_address1 || settings.billto_address1;
    document.getElementById('inv_billto_address2').value = jobDefaults.bill_to_address2 || settings.billto_address2;

    // Clear date fields (user should set these)
    document.getElementById('inv_start_date').value = '';
    document.getElementById('inv_end_date').value = '';

    // Show modal
    const modal = document.getElementById('invoiceModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

// Close invoice modal
function closeInvoiceModal() {
    const modal = document.getElementById('invoiceModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Handle invoice form submission
async function handleInvoiceSubmit(e) {
    e.preventDefault();

    // Collect form data
    const formData = {
        job_number: document.getElementById('inv_job_number').value,
        job_name: document.getElementById('inv_job_name').value,
        invoice_number: document.getElementById('inv_invoice_number').value,
        purchase_order: document.getElementById('inv_purchase_order').value || null,
        payment_terms_days: parseInt(document.getElementById('inv_payment_terms').value),
        ship_to_location: document.getElementById('inv_ship_to').value,
        contract_number: document.getElementById('inv_contract_number').value || null,
        company_name: document.getElementById('inv_company_name').value,
        company_address_line1: document.getElementById('inv_company_address1').value,
        company_address_line2: document.getElementById('inv_company_address2').value,
        company_phone: document.getElementById('inv_company_phone').value,
        company_fax: document.getElementById('inv_company_fax').value || null,
        bill_to_name: document.getElementById('inv_billto_name').value,
        bill_to_address_line1: document.getElementById('inv_billto_address1').value,
        bill_to_address_line2: document.getElementById('inv_billto_address2').value,
        start_date: document.getElementById('inv_start_date').value || null,
        end_date: document.getElementById('inv_end_date').value || null,
        aggregation_method: document.getElementById('inv_aggregation_method').value
    };

    // Save settings for next time
    saveInvoiceSettings({
        ship_to: formData.ship_to_location,
        billto_name: formData.bill_to_name,
        billto_address1: formData.bill_to_address_line1,
        billto_address2: formData.bill_to_address_line2,
        contract_number: formData.contract_number || '',
        payment_terms: formData.payment_terms_days.toString(),
        aggregation_method: formData.aggregation_method
    });

    // Show loading state
    const modalContent = document.querySelector('.modal-content');
    modalContent.classList.add('loading');

    try {
        const response = await fetch(`${window.API_BASE}/invoice/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            // Download the PDF
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Generate filename
            a.download = `Invoice_${formData.invoice_number}_${formData.job_number}.pdf`;

            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            // Close modal and show success
            closeInvoiceModal();

            // Show success message (requires showMessage function from app.js)
            if (typeof showMessage === 'function') {
                showMessage('Invoice generated successfully!', 'success');
            }
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Unknown error');
        }
    } catch (error) {
        console.error('Error generating invoice:', error);
        alert('Failed to generate invoice: ' + error.message);
    } finally {
        // Remove loading state
        modalContent.classList.remove('loading');
    }
}

// Initialize invoice module
function initInvoiceModule() {
    // Setup form submit handler
    const invoiceForm = document.getElementById('invoiceForm');
    if (invoiceForm) {
        invoiceForm.addEventListener('submit', handleInvoiceSubmit);
    }

    // Setup invoice button
    const invoiceBtn = document.getElementById('generateInvoiceBtn');
    if (invoiceBtn) {
        invoiceBtn.addEventListener('click', openInvoiceModal);
    }

    // Close modal when clicking outside
    window.addEventListener('click', function (event) {
        const modal = document.getElementById('invoiceModal');
        if (event.target === modal) {
            closeInvoiceModal();
        }
    });

    // Close modal on ESC key
    window.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            const modal = document.getElementById('invoiceModal');
            if (modal && modal.classList.contains('show')) {
                closeInvoiceModal();
            }
        }
    });

    console.log('âœ“ Invoice module initialized');
}

// Export module functions to window for external access
window.InvoiceModule = {
    init: initInvoiceModule,
    open: openInvoiceModal,
    close: closeInvoiceModal
};

// Verify export
console.log('📦 InvoiceModule exported:', {
    hasInit: typeof window.InvoiceModule.init === 'function',
    hasOpen: typeof window.InvoiceModule.open === 'function',
    hasClose: typeof window.InvoiceModule.close === 'function'
});

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initInvoiceModule);
} else {
    initInvoiceModule();
}