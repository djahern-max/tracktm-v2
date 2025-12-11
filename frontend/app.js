// TrackTM - Daily Timesheet Entry Application
const API_BASE = 'http://localhost:8000/api';

let materials = [];
let currentEntry = null;

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    // Set today's date as default
    document.getElementById('entryDate').valueAsDate = new Date();

    // Load materials catalog
    await loadMaterials();

    // Setup event listeners
    document.getElementById('loadBtn').addEventListener('click', loadEntry);
    document.getElementById('newBtn').addEventListener('click', newEntry);
    document.getElementById('saveBtn').addEventListener('click', saveEntry);
    document.getElementById('exportBtn').addEventListener('click', exportJob);
    document.getElementById('exportDetailedBtn').addEventListener('click', exportDetailed);
}

// Load materials catalog from API
async function loadMaterials() {
    try {
        const response = await fetch(`${API_BASE}/materials`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        materials = data;
        console.log(`Loaded ${materials.length} materials`);
    } catch (error) {
        console.error('Error loading materials:', error);
        alert('Failed to load materials catalog. Make sure the backend is running on port 8000.');
    }
}

// Load existing entry for selected date
async function loadEntry() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;

    if (!jobNumber || !entryDate) {
        alert('Please enter job number and date');
        return;
    }

    // Load saved company and job names for this job number
    loadJobInfo(jobNumber);

    try {
        const response = await fetch(`${API_BASE}/entries/${jobNumber}/${entryDate}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.entry) {
            currentEntry = data.entry;
            displayForm(currentEntry.line_items);
            showMessage(`Loaded entry for ${entryDate}`, 'success');
        } else {
            showMessage(`No entry found for ${entryDate}. Starting new entry.`, 'info');
            newEntry();
        }
    } catch (error) {
        console.error('Error loading entry:', error);
        alert('Failed to load entry: ' + error.message);
    }
}

// Create new entry form
function newEntry() {
    const jobNumber = document.getElementById('jobNumber').value;

    // Load saved company and job names if available
    if (jobNumber) {
        loadJobInfo(jobNumber);
    }

    currentEntry = null;
    displayForm([]);
    document.getElementById('actionsBar').style.display = 'flex';
}

// Save job info (company name and job name) to localStorage
function saveJobInfo(jobNumber, companyName, jobName) {
    if (!jobNumber) return;

    const jobInfo = {
        companyName: companyName,
        jobName: jobName
    };

    localStorage.setItem(`tracktm_job_${jobNumber}`, JSON.stringify(jobInfo));
}

// Load job info from localStorage
function loadJobInfo(jobNumber) {
    if (!jobNumber) return;

    const saved = localStorage.getItem(`tracktm_job_${jobNumber}`);
    if (saved) {
        try {
            const jobInfo = JSON.parse(saved);
            if (jobInfo.companyName) {
                document.getElementById('companyName').value = jobInfo.companyName;
            }
            if (jobInfo.jobName) {
                document.getElementById('jobName').value = jobInfo.jobName;
            }
        } catch (error) {
            console.error('Error loading job info:', error);
        }
    }
}

// Display the form with materials grouped by category
function displayForm(existingLineItems = []) {
    const container = document.getElementById('formContainer');
    container.innerHTML = '';

    // Group materials by category
    const byCategory = {};
    materials.forEach(mat => {
        if (!byCategory[mat.category]) {
            byCategory[mat.category] = [];
        }
        byCategory[mat.category].push(mat);
    });

    // Create form for each category
    Object.entries(byCategory).forEach(([category, items]) => {
        const section = createCategorySection(category, items, existingLineItems);
        container.appendChild(section);
    });

    // Show actions bar
    document.getElementById('actionsBar').style.display = 'flex';

    // Setup quantity input listeners
    setupQuantityListeners();

    // Calculate initial totals
    calculateTotal();
}

// Create a category section
function createCategorySection(category, items, existingLineItems) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = category;
    section.appendChild(header);

    const table = document.createElement('table');
    table.className = 'materials-table';

    // Table header
    table.innerHTML = `
        <thead>
            <tr>
                <th style="width: 40%">Material</th>
                <th style="width: 10%">Unit</th>
                <th style="width: 15%">QTY</th>
                <th style="width: 15%">Price</th>
                <th style="width: 20%; text-align: right;">Total</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');

    // Add row for each item
    items.forEach(item => {
        const existingItem = existingLineItems.find(li => li.material_id === item.id);
        const quantity = existingItem ? existingItem.quantity : 0;
        const unitPrice = existingItem ? existingItem.unit_price : item.unit_price;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="material-name">${item.name}</td>
            <td class="material-unit">${item.unit}</td>
            <td>
                <input 
                    type="number" 
                    class="qty-input" 
                    data-material-id="${item.id}"
                    value="${quantity > 0 ? quantity : ''}"
                    min="0"
                    step="0.01"
                    placeholder="0"
                />
            </td>
            <td>
                <input 
                    type="number" 
                    class="price-input" 
                    data-material-id="${item.id}"
                    value="${unitPrice}"
                    min="0"
                    step="0.01"
                />
            </td>
            <td class="item-total" data-material-id="${item.id}">
                $${(quantity * unitPrice).toFixed(2)}
            </td>
        `;
        tbody.appendChild(row);
    });

    section.appendChild(table);
    return section;
}

// Setup quantity and price input listeners
function setupQuantityListeners() {
    document.querySelectorAll('.qty-input, .price-input').forEach(input => {
        input.addEventListener('input', (e) => {
            const materialId = e.target.dataset.materialId;
            updateLineTotal(materialId);
            calculateTotal();
        });
    });
}

// Update line item total
function updateLineTotal(materialId) {
    const qtyInput = document.querySelector(`.qty-input[data-material-id="${materialId}"]`);
    const priceInput = document.querySelector(`.price-input[data-material-id="${materialId}"]`);
    const totalCell = document.querySelector(`.item-total[data-material-id="${materialId}"]`);

    const qty = parseFloat(qtyInput.value) || 0;
    const price = parseFloat(priceInput.value) || 0;
    const total = qty * price;

    totalCell.textContent = `$${total.toFixed(2)}`;
}

// Calculate and display grand total
function calculateTotal() {
    let grandTotal = 0;

    document.querySelectorAll('.qty-input').forEach(input => {
        const materialId = input.dataset.materialId;
        const qty = parseFloat(input.value) || 0;
        const priceInput = document.querySelector(`.price-input[data-material-id="${materialId}"]`);
        const price = parseFloat(priceInput.value) || 0;
        grandTotal += (qty * price);
    });

    document.getElementById('dailyTotal').textContent = `$${grandTotal.toFixed(2)}`;
}

// Save entry
async function saveEntry() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;
    const companyName = document.getElementById('companyName').value;
    const jobName = document.getElementById('jobName').value;

    if (!jobNumber || !entryDate) {
        alert('Please enter job number and date');
        return;
    }

    // Save company and job names for this job number
    saveJobInfo(jobNumber, companyName, jobName);

    // Collect line items (only non-zero quantities)
    const lineItems = [];
    document.querySelectorAll('.qty-input').forEach(input => {
        const qty = parseFloat(input.value) || 0;
        if (qty > 0) {
            const materialId = parseInt(input.dataset.materialId);
            const priceInput = document.querySelector(`.price-input[data-material-id="${materialId}"]`);
            const unitPrice = parseFloat(priceInput.value);

            lineItems.push({
                material_id: materialId,
                quantity: qty,
                unit_price: unitPrice
            });
        }
    });

    if (lineItems.length === 0) {
        alert('Please enter at least one quantity');
        return;
    }

    console.log('Saving entry:', { job_number: jobNumber, entry_date: entryDate, line_items: lineItems });

    // Save to API
    try {
        const response = await fetch(`${API_BASE}/entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_number: jobNumber,
                entry_date: entryDate,
                line_items: lineItems
            })
        });

        const data = await response.json();
        console.log('Save response:', data);

        if (response.ok) {
            const total = data.entry.line_items.reduce((sum, item) => sum + item.total_amount, 0);
            showMessage(`Entry saved successfully! Total: $${total.toFixed(2)}`, 'success');
            currentEntry = data.entry;
        } else {
            console.error('Save failed:', data);
            alert('Failed to save entry: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving entry:', error);
        alert('Failed to save entry: ' + error.message);
    }
}

// Helper functions for formatting
function formatCurrency(amount) {
    // Format without commas for CSV compatibility
    return '$' + amount.toFixed(2);
}

// Export job summary
async function exportJob() {
    const jobNumber = document.getElementById('jobNumber').value;
    const companyName = document.getElementById('companyName').value || 'Company Name';
    const jobName = document.getElementById('jobName').value || '';

    if (!jobNumber) {
        alert('Please enter job number');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/entries?job_number=${jobNumber}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const entriesData = await response.json();

        if (entriesData.entries && entriesData.entries.length > 0) {
            const summary = calculateSummary(entriesData.entries, jobNumber);
            const csv = generateEnhancedCSV(summary, companyName, jobName);

            // Use report date range for filename instead of today's date
            const dates = entriesData.entries.map(e => e.entry_date).sort();
            const lastDate = dates[dates.length - 1].replace(/-/g, '-'); // Keep as YYYY-MM-DD

            downloadCSV(csv, `Job_${jobNumber}_Summary_${lastDate}.csv`);
            showMessage('Summary exported successfully!', 'success');
        } else {
            alert('No entries found for this job');
        }
    } catch (error) {
        console.error('Error exporting:', error);
        alert('Failed to export job summary: ' + error.message);
    }
}

// Enhanced detailed export with breakdown by category
async function exportDetailed() {
    const jobNumber = document.getElementById('jobNumber').value;
    const companyName = document.getElementById('companyName').value || 'Company Name';
    const jobName = document.getElementById('jobName').value || '';

    if (!jobNumber) {
        alert('Please enter job number');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/entries?job_number=${jobNumber}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const entriesData = await response.json();

        if (entriesData.entries && entriesData.entries.length > 0) {
            const summary = calculateSummary(entriesData.entries, jobNumber);
            const csv = generateDetailedCSV(summary, entriesData.entries, companyName, jobName);

            // Use report date range for filename instead of today's date
            const dates = entriesData.entries.map(e => e.entry_date).sort();
            const lastDate = dates[dates.length - 1].replace(/-/g, '-'); // Keep as YYYY-MM-DD

            downloadCSV(csv, `Job_${jobNumber}_Detailed_${lastDate}.csv`);
            showMessage('Detailed report exported successfully!', 'success');
        } else {
            alert('No entries found for this job');
        }
    } catch (error) {
        console.error('Error exporting:', error);
        alert('Failed to export detailed report: ' + error.message);
    }
}

// Calculate summary from entries
function calculateSummary(entries, jobNumber) {
    let grandTotal = 0;
    const entriesSummary = [];

    entries.forEach(entry => {
        const entryTotal = entry.line_items.reduce((sum, item) => sum + item.total_amount, 0);
        grandTotal += entryTotal;
        entriesSummary.push({
            date: entry.entry_date,
            item_count: entry.line_items.length,
            total: entryTotal
        });
    });

    return {
        job_number: jobNumber,
        total_days: entries.length,
        grand_total: grandTotal,
        entries: entriesSummary.sort((a, b) => a.date.localeCompare(b.date))
    };
}

// Generate enhanced summary CSV (Excel/Numbers compatible)
function generateEnhancedCSV(summary, companyName, jobName) {
    const lines = [];
    const today = new Date();
    const reportDate = today.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    // Header
    lines.push(companyName);
    lines.push('Time & Materials Summary Report');
    lines.push('');
    lines.push(`Job Number:,${summary.job_number}`);
    if (jobName) lines.push(`Job Name:,${jobName}`);
    lines.push(`Report Generated:,${reportDate}`);
    lines.push('');

    // Summary
    lines.push('SUMMARY');
    lines.push('=====================================');
    lines.push(`Total Days:,${summary.total_days}`);
    lines.push(`Grand Total:,${formatCurrency(summary.grand_total)}`);
    lines.push('');

    // Daily breakdown
    lines.push('DAILY BREAKDOWN');
    lines.push('=====================================');
    lines.push('Date,Day,Items,Daily Total');

    summary.entries.forEach(entry => {
        // Parse date correctly to avoid timezone issues
        // entry.date is in format "YYYY-MM-DD"
        const [year, month, day] = entry.date.split('-').map(Number);
        const date = new Date(year, month - 1, day); // month is 0-indexed

        const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
        const formattedDate = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        lines.push(`${formattedDate},${dayName},${entry.item_count},${formatCurrency(entry.total)}`);
    });

    lines.push('=====================================');
    lines.push(`TOTAL:,,${summary.entries.reduce((sum, e) => sum + e.item_count, 0)},${formatCurrency(summary.grand_total)}`);

    return lines.join('\n');
}

// Generate detailed breakdown CSV (Excel/Numbers compatible)
function generateDetailedCSV(summary, entries, companyName, jobName) {
    const lines = [];
    const today = new Date();
    const reportDate = today.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    // Calculate date range from entries
    const dates = entries.map(e => e.entry_date).sort();
    const firstDate = dates[0];
    const lastDate = dates[dates.length - 1];

    // Parse dates correctly to avoid timezone issues
    const [y1, m1, d1] = firstDate.split('-').map(Number);
    const [y2, m2, d2] = lastDate.split('-').map(Number);
    const startDate = new Date(y1, m1 - 1, d1);
    const endDate = new Date(y2, m2 - 1, d2);

    const formattedStartDate = startDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
    const formattedEndDate = endDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    // Header
    lines.push(companyName);
    lines.push('Time & Materials Detailed Report');
    lines.push('');
    lines.push(`Job Number:,${summary.job_number}`);
    if (jobName) lines.push(`Job Name:,${jobName}`);
    lines.push(`Report Period:,${formattedStartDate} - ${formattedEndDate}`);
    lines.push(`Report Generated:,${reportDate}`);
    lines.push('');

    // Aggregate items across all days by category
    const itemTotals = {};

    entries.forEach(entry => {
        entry.line_items.forEach(item => {
            const key = `${item.category}|${item.material_name}|${item.unit}|${item.unit_price}`;
            if (!itemTotals[key]) {
                itemTotals[key] = {
                    category: item.category,
                    name: item.material_name,
                    unit: item.unit,
                    unit_price: item.unit_price,
                    total_quantity: 0,
                    total_amount: 0
                };
            }
            itemTotals[key].total_quantity += item.quantity;
            itemTotals[key].total_amount += item.total_amount;
        });
    });

    // Group by category
    const byCategory = {};
    Object.values(itemTotals).forEach(item => {
        if (!byCategory[item.category]) {
            byCategory[item.category] = [];
        }
        byCategory[item.category].push(item);
    });

    // Category order
    const categoryOrder = ['EQUIPMENT', 'MATERIALS', 'PPE', 'CONSUMABLES', 'FUEL'];

    // Output by category
    lines.push('DETAILED BREAKDOWN BY CATEGORY');
    lines.push('=============================================================');
    lines.push('');

    categoryOrder.forEach(category => {
        if (byCategory[category]) {
            lines.push(category);
            lines.push('-------------------------------------------------------------');
            lines.push('Item,Unit,Quantity,Unit Price,Total');

            byCategory[category].forEach(item => {
                // Format quantity to avoid unnecessary decimals
                const qty = item.total_quantity % 1 === 0 ? item.total_quantity.toFixed(0) : item.total_quantity.toFixed(2);
                lines.push(`"${item.name}",${item.unit},${qty},${formatCurrency(item.unit_price)},${formatCurrency(item.total_amount)}`);
            });

            const categoryTotal = byCategory[category].reduce((sum, item) => sum + item.total_amount, 0);
            lines.push(`${category} SUBTOTAL:,,,${formatCurrency(categoryTotal)}`);
            lines.push('');
        }
    });

    lines.push('=============================================================');
    lines.push(`GRAND TOTAL:,,,${formatCurrency(summary.grand_total)}`);

    return lines.join('\n');
}

// Download CSV with proper encoding
function downloadCSV(csv, filename) {
    // Use UTF-8 BOM for proper Excel/Numbers handling
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Show message
function showMessage(message, type = 'info') {
    // Remove any existing messages
    document.querySelectorAll('.success-message, .error-message, .info-message').forEach(msg => msg.remove());

    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'success' ? 'success-message' : (type === 'error' ? 'error-message' : 'info-message');
    messageDiv.textContent = message;

    const container = document.querySelector('.form-container');
    container.insertBefore(messageDiv, container.firstChild);

    setTimeout(() => messageDiv.remove(), 5000);
}