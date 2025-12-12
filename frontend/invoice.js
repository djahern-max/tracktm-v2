// Invoice Generation Module
// Handles invoice modal, form validation, and PDF generation
// Note: Uses API_BASE from app.js (must be loaded after app.js)

// Load saved invoice settings from localStorage
function loadInvoiceSettings() {
    return {
        company_name: localStorage.getItem('inv_company_name') || 'Tri-State Painting, LLC (TSI)',
        company_address1: localStorage.getItem('inv_company_address1') || '612 West Main Street Unit 2',
        company_address2: localStorage.getItem('inv_company_address2') || 'Tilton, NH 03276',
        company_phone: localStorage.getItem('inv_company_phone') || '(603) 286-7657',
        company_fax: localStorage.getItem('inv_company_fax') || '(603) 286-7882',
        billto_name: localStorage.getItem('inv_billto_name') || 'Reagan Marine Construction LLC',
        billto_address1: localStorage.getItem('inv_billto_address1') || '221 Third St, 5th Floor Suite 513',
        billto_address2: localStorage.getItem('inv_billto_address2') || 'Newport, RI 02840',
        remit_email: localStorage.getItem('inv_remit_email') || 'AP@reaganmarine.com',
        ship_to: localStorage.getItem('inv_ship_to') || 'Newport, RI',
        payment_terms: localStorage.getItem('inv_payment_terms') || '30'
    };
}

// Save invoice settings to localStorage
function saveInvoiceSettings(data) {
    localStorage.setItem('inv_company_name', data.company_name);
    localStorage.setItem('inv_company_address1', data.company_address1);
    localStorage.setItem('inv_company_address2', data.company_address2);
    localStorage.setItem('inv_company_phone', data.company_phone);
    localStorage.setItem('inv_company_fax', data.company_fax);
    localStorage.setItem('inv_billto_name', data.billto_name);
    localStorage.setItem('inv_billto_address1', data.billto_address1);
    localStorage.setItem('inv_billto_address2', data.billto_address2);
    localStorage.setItem('inv_remit_email', data.remit_email);
    localStorage.setItem('inv_ship_to', data.ship_to);
    localStorage.setItem('inv_payment_terms', data.payment_terms);
}

// Open invoice modal and populate with saved/current values
function openInvoiceModal() {
    const jobNumber = document.getElementById('jobNumber').value;
    const jobName = document.getElementById('jobName').value;

    if (!jobNumber) {
        alert('Please enter job number');
        return;
    }

    // Load saved settings
    const settings = loadInvoiceSettings();

    // Get date range from header (if set)
    const startDate = document.getElementById('periodStart')?.value || '';
    const endDate = document.getElementById('periodEnd')?.value || '';

    // Populate form
    document.getElementById('inv_job_number').value = jobNumber;
    document.getElementById('inv_job_name').value = jobName || `Job ${jobNumber}`;
    document.getElementById('inv_purchase_order').value = '';
    document.getElementById('inv_payment_terms').value = settings.payment_terms;
    document.getElementById('inv_remit_email').value = settings.remit_email;
    document.getElementById('inv_ship_to').value = settings.ship_to;

    // Company info (your company)
    document.getElementById('inv_company_name').value = settings.company_name;
    document.getElementById('inv_company_address1').value = settings.company_address1;
    document.getElementById('inv_company_address2').value = settings.company_address2;
    document.getElementById('inv_company_phone').value = settings.company_phone;
    document.getElementById('inv_company_fax').value = settings.company_fax;

    // Bill to info (client)
    document.getElementById('inv_billto_name').value = settings.billto_name;
    document.getElementById('inv_billto_address1').value = settings.billto_address1;
    document.getElementById('inv_billto_address2').value = settings.billto_address2;

    // PRE-FILL date range from header fields (if set)
    document.getElementById('inv_start_date').value = startDate;
    document.getElementById('inv_end_date').value = endDate;

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
        purchase_order: document.getElementById('inv_purchase_order').value,
        payment_terms_days: parseInt(document.getElementById('inv_payment_terms').value),
        remit_to_email: document.getElementById('inv_remit_email').value,
        ship_to_location: document.getElementById('inv_ship_to').value,
        company_name: document.getElementById('inv_company_name').value,
        company_address_line1: document.getElementById('inv_company_address1').value,
        company_address_line2: document.getElementById('inv_company_address2').value,
        company_phone: document.getElementById('inv_company_phone').value,
        company_fax: document.getElementById('inv_company_fax').value,
        bill_to_name: document.getElementById('inv_billto_name').value,
        bill_to_address_line1: document.getElementById('inv_billto_address1').value,
        bill_to_address_line2: document.getElementById('inv_billto_address2').value,
        start_date: document.getElementById('inv_start_date').value || null,
        end_date: document.getElementById('inv_end_date').value || null
    };

    // Save settings for next time
    saveInvoiceSettings({
        company_name: formData.company_name,
        company_address1: formData.company_address_line1,
        company_address2: formData.company_address_line2,
        company_phone: formData.company_phone,
        company_fax: formData.company_fax,
        billto_name: formData.bill_to_name,
        billto_address1: formData.bill_to_address_line1,
        billto_address2: formData.bill_to_address_line2,
        remit_email: formData.remit_to_email,
        ship_to: formData.ship_to_location,
        payment_terms: formData.payment_terms_days.toString()
    });

    // Show loading state
    const modalContent = document.querySelector('.modal-content');
    modalContent.classList.add('loading');

    try {
        const response = await fetch(`${API_BASE}/invoice/generate`, {
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
            const today = new Date();
            const dateStr = today.toISOString().split('T')[0];
            a.download = `Invoice_${formData.job_number}_${dateStr}.pdf`;

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
            if (modal.classList.contains('show')) {
                closeInvoiceModal();
            }
        }
    });

    console.log('✓ Invoice module initialized');
}

// Export functions for use in app.js
window.InvoiceModule = {
    open: openInvoiceModal,
    close: closeInvoiceModal,
    init: initInvoiceModule
};