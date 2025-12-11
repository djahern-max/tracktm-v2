// TrackTM - Daily Timesheet Entry Application
// UPDATED: Multiple Employees Per Labor Role Support + CSV Export with Labor
const API_BASE = 'http://localhost:8000/api';

let materials = [];
let laborRoles = [];
let currentEntry = null;
let laborRowCounter = 0; // For unique row IDs

// ============================================
// HELPER FUNCTIONS - ADD THESE THREE HERE ⬇️
// ============================================

// Helper function to get date range from header fields
function getDateRange() {
    const startDate = document.getElementById('periodStart')?.value || null;
    const endDate = document.getElementById('periodEnd')?.value || null;
    return { startDate, endDate };
}

// Helper function to filter entries by date range
function filterEntriesByDateRange(entries, startDate, endDate) {
    let filtered = entries;

    if (startDate) {
        filtered = filtered.filter(e => e.entry_date >= startDate);
    }
    if (endDate) {
        filtered = filtered.filter(e => e.entry_date <= endDate);
    }

    return filtered;
}

// Helper function to generate filename with date range
function generateFilename(jobNumber, type, startDate, endDate, entries) {
    let filename = `Job_${jobNumber}_${type}`;

    if (startDate && endDate) {
        filename += `_${startDate}_to_${endDate}`;
    } else if (startDate) {
        filename += `_from_${startDate}`;
    } else if (endDate) {
        filename += `_to_${endDate}`;
    } else if (entries && entries.length > 0) {
        const dates = entries.map(e => e.entry_date).sort();
        const lastDate = dates[dates.length - 1];
        filename += `_${lastDate}`;
    }

    return filename + '.csv';
}


// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    // Set today's date as default
    document.getElementById('entryDate').valueAsDate = new Date();

    // Load materials catalog and labor roles
    await loadMaterials();
    await loadLaborRoles();

    // Setup event listeners
    document.getElementById('loadBtn').addEventListener('click', loadEntry);
    document.getElementById('newBtn').addEventListener('click', newEntry);
    document.getElementById('saveBtn').addEventListener('click', saveEntry);
    document.getElementById('exportCurrentDayBtn').addEventListener('click', exportCurrentDay);
    document.getElementById('exportBtn').addEventListener('click', exportJob);
    document.getElementById('exportDetailedBtn').addEventListener('click', exportDetailed);
    document.getElementById('generateInvoiceBtn').addEventListener('click', openInvoiceModal);
}

async function loadLaborRoles() {
    try {
        const response = await fetch(`${API_BASE}/labor-roles`);
        const data = await response.json();
        laborRoles = data;
        console.log(`Loaded ${laborRoles.length} labor roles`);
    } catch (error) {
        console.error('Error loading labor roles:', error);
        alert('Failed to load labor roles. Make sure the backend is running.');
    }
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
            displayForm(currentEntry.line_items, currentEntry.labor_entries || []);
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
    displayForm([], []);
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
function displayForm(existingLineItems = [], existingLaborItems = []) {
    const container = document.getElementById('formContainer');
    container.innerHTML = '';
    laborRowCounter = 0;

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

    // Add labor section with multiple employee support
    const laborSection = createLaborSection(existingLaborItems);
    container.appendChild(laborSection);

    // Show actions bar
    document.getElementById('actionsBar').style.display = 'flex';

    // Setup quantity input listeners
    setupQuantityListeners();

    // ============================================
    // FIX: Force recalculate all labor totals after form loads
    // ============================================
    laborRoles.forEach(role => {
        const rows = document.querySelectorAll(`.employee-row[data-role-id="${role.id}"]`);
        rows.forEach(row => {
            const rowId = row.getAttribute('data-row-id');
            updateEmployeeTotal(rowId, role);
        });
    });

    // Calculate initial totals (this now includes the labor totals we just calculated)
    calculateTotal();
}

function createLaborSection(existingLaborItems = []) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = 'LABOR';
    section.appendChild(header);

    // Group existing labor items by role
    const laborByRole = {};
    existingLaborItems.forEach(item => {
        if (!laborByRole[item.labor_role_id]) {
            laborByRole[item.labor_role_id] = [];
        }
        laborByRole[item.labor_role_id].push(item);
    });

    // Create a subsection for each role
    laborRoles.forEach(role => {
        const roleSection = createLaborRoleSection(role, laborByRole[role.id] || []);
        section.appendChild(roleSection);
    });

    return section;
}

function createLaborRoleSection(role, existingEmployees = []) {
    const roleSection = document.createElement('div');
    roleSection.className = 'labor-role-section';
    roleSection.setAttribute('data-role-id', role.id);

    // Role header with add button
    const roleHeader = document.createElement('div');
    roleHeader.className = 'labor-role-header';
    roleHeader.innerHTML = `
        <span class="role-name">${role.name} (${formatCurrency(role.straight_rate)}/hr Reg, ${formatCurrency(role.overtime_rate)}/hr OT)</span>
        <button class="btn-add-employee" data-role-id="${role.id}">+ Add ${role.name}</button>
    `;
    roleSection.appendChild(roleHeader);

    // Container for employee rows
    const employeesContainer = document.createElement('div');
    employeesContainer.className = 'employees-container';
    employeesContainer.setAttribute('data-role-id', role.id);

    // Add existing employees or show empty state
    if (existingEmployees.length > 0) {
        existingEmployees.forEach(emp => {
            const row = createEmployeeRow(role, emp);
            employeesContainer.appendChild(row);
        });
    } else {
        employeesContainer.innerHTML = '<div class="empty-state">No employees added. Click "+ Add" to add an employee.</div>';
    }

    roleSection.appendChild(employeesContainer);

    // Add employee button click handler
    roleHeader.querySelector('.btn-add-employee').addEventListener('click', () => {
        addEmployeeRow(role);
    });

    return roleSection;
}

function addEmployeeRow(role) {
    const container = document.querySelector(`.employees-container[data-role-id="${role.id}"]`);

    // Remove empty state if it exists
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    // Load last used employee name for this role
    const lastEmployee = loadEmployeeName(role.id);

    const row = createEmployeeRow(role, {
        employee_name: lastEmployee,
        regular_hours: 0,
        overtime_hours: 0,
        night_shift: false
    });

    container.appendChild(row);
    calculateTotal();
}

function createEmployeeRow(role, employeeData = {}) {
    laborRowCounter++;
    const rowId = `labor-row-${laborRowCounter}`;

    const row = document.createElement('div');
    row.className = 'employee-row';
    row.setAttribute('data-row-id', rowId);
    row.setAttribute('data-role-id', role.id);

    const employeeName = employeeData.employee_name || '';
    const regHours = employeeData.regular_hours || 0;
    const otHours = employeeData.overtime_hours || 0;
    const nightShift = employeeData.night_shift || false;

    row.innerHTML = `
        <input 
            type="text" 
            class="employee-input" 
            data-row-id="${rowId}"
            value="${employeeName}"
            placeholder="Employee Name"
        />
        <input 
            type="number" 
            class="labor-reg-input" 
            data-row-id="${rowId}"
            value="${regHours > 0 ? regHours : ''}"
            min="0"
            step="0.5"
            placeholder="Reg Hrs"
        />
        <input 
            type="number" 
            class="labor-ot-input" 
            data-row-id="${rowId}"
            value="${otHours > 0 ? otHours : ''}"
            min="0"
            step="0.5"
            placeholder="OT Hrs"
        />
        <label class="night-shift-label">
            <input 
                type="checkbox" 
                class="night-shift-checkbox" 
                data-row-id="${rowId}"
                ${nightShift ? 'checked' : ''}
            />
            <span>Night</span>
        </label>
        <div class="labor-total" data-row-id="${rowId}">$0.00</div>
        <button class="btn-remove-employee" data-row-id="${rowId}">×</button>
    `;

    // Setup event listeners
    const regInput = row.querySelector('.labor-reg-input');
    const otInput = row.querySelector('.labor-ot-input');
    const nightCheckbox = row.querySelector('.night-shift-checkbox');
    const employeeInput = row.querySelector('.employee-input');

    [regInput, otInput, nightCheckbox].forEach(input => {
        input.addEventListener('input', () => {
            updateEmployeeTotal(rowId, role);
            calculateTotal();
        });
    });

    // Save employee name when it changes
    employeeInput.addEventListener('blur', () => {
        if (employeeInput.value) {
            saveEmployeeName(role.id, employeeInput.value);
        }
    });

    // Remove button
    row.querySelector('.btn-remove-employee').addEventListener('click', () => {
        row.remove();

        // If no more employees, show empty state
        const container = document.querySelector(`.employees-container[data-role-id="${role.id}"]`);
        if (container.children.length === 0) {
            container.innerHTML = '<div class="empty-state">No employees added. Click "+ Add" to add an employee.</div>';
        }

        calculateTotal();
    });

    // Calculate initial total
    setTimeout(() => updateEmployeeTotal(rowId, role), 0);

    return row;
}

function updateEmployeeTotal(rowId, role) {
    const regInput = document.querySelector(`.labor-reg-input[data-row-id="${rowId}"]`);
    const otInput = document.querySelector(`.labor-ot-input[data-row-id="${rowId}"]`);
    const nightCheckbox = document.querySelector(`.night-shift-checkbox[data-row-id="${rowId}"]`);
    const totalCell = document.querySelector(`.labor-total[data-row-id="${rowId}"]`);

    if (!regInput || !otInput || !nightCheckbox || !totalCell) return;

    const regHours = parseFloat(regInput.value) || 0;
    const otHours = parseFloat(otInput.value) || 0;
    const nightShift = nightCheckbox.checked;

    let regRate = role.straight_rate;
    let otRate = role.overtime_rate;

    if (nightShift) {
        regRate += 2.00;
        otRate += 2.00;
    }

    const total = (regHours * regRate) + (otHours * otRate);
    totalCell.textContent = formatCurrency(total);
}

function saveEmployeeName(laborRoleId, employeeName) {
    localStorage.setItem(`tracktm_labor_${laborRoleId}`, employeeName);
}

function loadEmployeeName(laborRoleId) {
    return localStorage.getItem(`tracktm_labor_${laborRoleId}`) || '';
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

    totalCell.textContent = formatCurrency(total);
}

// Calculate and display grand total (materials + labor)
function calculateTotal() {
    let grandTotal = 0;

    // Materials
    document.querySelectorAll('.qty-input').forEach(input => {
        const materialId = input.dataset.materialId;
        const qty = parseFloat(input.value) || 0;
        const priceInput = document.querySelector(`.price-input[data-material-id="${materialId}"]`);
        const price = parseFloat(priceInput.value) || 0;
        grandTotal += (qty * price);
    });

    // Labor - sum all employee totals
    document.querySelectorAll('.labor-total').forEach(cell => {
        const total = parseFloat(cell.textContent.replace('$', '').replace(',', '')) || 0;
        grandTotal += total;
    });

    document.getElementById('dailyTotal').textContent = formatCurrency(grandTotal);
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

    // Collect labor items - ALL employee rows
    const laborItems = [];
    document.querySelectorAll('.employee-row').forEach(row => {
        const rowId = row.getAttribute('data-row-id');
        const roleId = parseInt(row.getAttribute('data-role-id'));

        const employeeInput = row.querySelector('.employee-input');
        const regInput = row.querySelector('.labor-reg-input');
        const otInput = row.querySelector('.labor-ot-input');
        const nightCheckbox = row.querySelector('.night-shift-checkbox');

        const regHours = parseFloat(regInput.value) || 0;
        const otHours = parseFloat(otInput.value) || 0;

        // Only save if there are hours
        if (regHours > 0 || otHours > 0) {
            laborItems.push({
                labor_role_id: roleId,
                employee_name: employeeInput.value || null,
                regular_hours: regHours,
                overtime_hours: otHours,
                night_shift: nightCheckbox.checked
            });
        }
    });

    if (lineItems.length === 0 && laborItems.length === 0) {
        alert('Please enter at least one material quantity or labor hours');
        return;
    }

    console.log('Saving entry:', {
        job_number: jobNumber,
        entry_date: entryDate,
        line_items: lineItems,
        labor_items: laborItems
    });

    // Save to API
    try {
        const response = await fetch(`${API_BASE}/entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_number: jobNumber,
                entry_date: entryDate,
                line_items: lineItems,
                labor_items: laborItems
            })
        });

        const data = await response.json();
        console.log('Save response:', data);

        if (response.ok) {
            const materialsTotal = data.entry.line_items.reduce((sum, item) => sum + item.total_amount, 0);
            const laborTotal = data.entry.labor_entries.reduce((sum, item) => sum + item.total_amount, 0);
            const grandTotal = materialsTotal + laborTotal;
            showMessage(`Entry saved successfully! Total: ${formatCurrency(grandTotal)}`, 'success');
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

    // Get date range from header fields
    const { startDate, endDate } = getDateRange();

    // Show what's being exported
    if (startDate || endDate) {
        const rangeMsg = `Exporting ${startDate || 'beginning'} to ${endDate || 'end'}`;
        console.log(rangeMsg);
    }

    try {
        const response = await fetch(`${API_BASE}/entries?job_number=${jobNumber}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const entriesData = await response.json();

        if (entriesData.entries && entriesData.entries.length > 0) {
            // Filter entries by date range
            const filteredEntries = filterEntriesByDateRange(entriesData.entries, startDate, endDate);

            if (filteredEntries.length === 0) {
                alert('No entries found for the specified date range');
                return;
            }

            const summary = calculateSummary(filteredEntries, jobNumber);
            const csv = generateEnhancedCSV(summary, companyName, jobName);
            const filename = generateFilename(jobNumber, 'Summary', startDate, endDate, filteredEntries);

            downloadCSV(csv, filename);
            showMessage(`Summary exported: ${filteredEntries.length} days`, 'success');
        } else {
            alert('No entries found for this job');
        }
    } catch (error) {
        console.error('Error exporting:', error);
        alert('Failed to export job summary: ' + error.message);
    }
}

// Enhanced detailed export WITH LABOR
async function exportDetailed() {
    const jobNumber = document.getElementById('jobNumber').value;
    const companyName = document.getElementById('companyName').value || 'Company Name';
    const jobName = document.getElementById('jobName').value || '';

    if (!jobNumber) {
        alert('Please enter job number');
        return;
    }

    // Get date range from header fields
    const { startDate, endDate } = getDateRange();

    // Show what's being exported
    if (startDate || endDate) {
        const rangeMsg = `Exporting ${startDate || 'beginning'} to ${endDate || 'end'}`;
        console.log(rangeMsg);
    }

    try {
        const response = await fetch(`${API_BASE}/entries?job_number=${jobNumber}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const entriesData = await response.json();

        if (entriesData.entries && entriesData.entries.length > 0) {
            // Filter entries by date range
            const filteredEntries = filterEntriesByDateRange(entriesData.entries, startDate, endDate);

            if (filteredEntries.length === 0) {
                alert('No entries found for the specified date range');
                return;
            }

            const summary = calculateSummary(filteredEntries, jobNumber);
            const csv = generateDetailedCSV(summary, filteredEntries, companyName, jobName, startDate, endDate);
            const filename = generateFilename(jobNumber, 'Detailed', startDate, endDate, filteredEntries);

            downloadCSV(csv, filename);
            showMessage(`Detailed report exported: ${filteredEntries.length} days`, 'success');
        } else {
            alert('No entries found for this job');
        }
    } catch (error) {
        console.error('Error exporting:', error);
        alert('Failed to export detailed report: ' + error.message);
    }
}

// NEW: Export just the currently loaded day
async function exportCurrentDay() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;
    const companyName = document.getElementById('companyName').value || 'Company Name';
    const jobName = document.getElementById('jobName').value || '';

    if (!jobNumber || !entryDate) {
        alert('Please load an entry first');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/entries?job_number=${jobNumber}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const entriesData = await response.json();

        if (entriesData.entries && entriesData.entries.length > 0) {
            // Filter to ONLY the currently loaded date
            const filteredEntries = entriesData.entries.filter(e => e.entry_date === entryDate);

            if (filteredEntries.length === 0) {
                alert('No entry found for this date');
                return;
            }

            const summary = calculateSummary(filteredEntries, jobNumber);
            const csv = generateDetailedCSV(summary, filteredEntries, companyName, jobName);
            const filename = `Job_${jobNumber}_${entryDate}.csv`;

            downloadCSV(csv, filename);
            showMessage(`Exported ${entryDate}`, 'success');
        } else {
            alert('No entries found for this job');
        }
    } catch (error) {
        console.error('Error exporting:', error);
        alert('Failed to export: ' + error.message);
    }
}

// Calculate summary from entries
function calculateSummary(entries, jobNumber) {
    let grandTotal = 0;
    const entriesSummary = [];

    entries.forEach(entry => {
        const materialsTotal = entry.line_items.reduce((sum, item) => sum + item.total_amount, 0);
        const laborTotal = entry.labor_entries ? entry.labor_entries.reduce((sum, item) => sum + item.total_amount, 0) : 0;
        const entryTotal = materialsTotal + laborTotal;
        grandTotal += entryTotal;

        entriesSummary.push({
            date: entry.entry_date,
            item_count: entry.line_items.length + (entry.labor_entries ? entry.labor_entries.length : 0),
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

// Generate enhanced summary CSV
function generateEnhancedCSV(summary, companyName, jobName) {
    const lines = [];
    const today = new Date();
    const reportDate = today.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    lines.push(companyName);
    lines.push('Time & Materials Summary Report');
    lines.push('');
    lines.push(`Job Number:,${summary.job_number}`);
    if (jobName) lines.push(`Job Name:,${jobName}`);
    lines.push(`Report Generated:,${reportDate}`);
    lines.push('');
    lines.push('SUMMARY');
    lines.push('=====================================');
    lines.push(`Total Days:,${summary.total_days}`);
    lines.push(`Grand Total:,${formatCurrency(summary.grand_total)}`);
    lines.push('');
    lines.push('DAILY BREAKDOWN');
    lines.push('=====================================');
    lines.push('Date,Day,Items,Daily Total');

    summary.entries.forEach(entry => {
        const [year, month, day] = entry.date.split('-').map(Number);
        const date = new Date(year, month - 1, day);
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

// Generate detailed breakdown CSV WITH LABOR
function generateDetailedCSV(summary, entries, companyName, jobName) {
    const lines = [];
    const today = new Date();
    const reportDate = today.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    const dates = entries.map(e => e.entry_date).sort();
    const firstDate = dates[0];
    const lastDate = dates[dates.length - 1];
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

    lines.push(companyName);
    lines.push('Time & Materials Detailed Report');
    lines.push('');
    lines.push(`Job Number:,${summary.job_number}`);
    if (jobName) lines.push(`Job Name:,${jobName}`);
    lines.push(`Report Period:,${formattedStartDate} - ${formattedEndDate}`);
    lines.push(`Report Generated:,${reportDate}`);
    lines.push('');

    // ========== MATERIALS SECTION ==========
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

    const byCategory = {};
    Object.values(itemTotals).forEach(item => {
        if (!byCategory[item.category]) {
            byCategory[item.category] = [];
        }
        byCategory[item.category].push(item);
    });

    const categoryOrder = ['EQUIPMENT', 'MATERIALS', 'PPE', 'CONSUMABLES', 'FUEL'];

    lines.push('MATERIALS BREAKDOWN');
    lines.push('=============================================================');
    lines.push('');

    let materialsGrandTotal = 0;

    categoryOrder.forEach(category => {
        if (byCategory[category]) {
            lines.push(category);
            lines.push('-------------------------------------------------------------');
            lines.push('Item,Unit,Quantity,Unit Price,Total');
            byCategory[category].forEach(item => {
                const qty = item.total_quantity % 1 === 0 ? item.total_quantity.toFixed(0) : item.total_quantity.toFixed(2);
                lines.push(`"${item.name}",${item.unit},${qty},${formatCurrency(item.unit_price)},${formatCurrency(item.total_amount)}`);
            });
            const categoryTotal = byCategory[category].reduce((sum, item) => sum + item.total_amount, 0);
            materialsGrandTotal += categoryTotal;
            lines.push(`${category} SUBTOTAL:,,,,${formatCurrency(categoryTotal)}`);
            lines.push('');
        }
    });

    lines.push('MATERIALS TOTAL:,,,,${formatCurrency(materialsGrandTotal)}');
    lines.push('');
    lines.push('');

    // ========== LABOR SECTION ==========
    const laborTotals = {};

    entries.forEach(entry => {
        if (entry.labor_entries) {
            entry.labor_entries.forEach(labor => {
                const key = `${labor.role_name}`;
                if (!laborTotals[key]) {
                    laborTotals[key] = {
                        role_name: labor.role_name,
                        regular_hours: 0,
                        overtime_hours: 0,
                        total_amount: 0,
                        employees: []
                    };
                }
                laborTotals[key].regular_hours += labor.regular_hours;
                laborTotals[key].overtime_hours += labor.overtime_hours;
                laborTotals[key].total_amount += labor.total_amount;

                // Track individual employees
                if (labor.employee_name) {
                    laborTotals[key].employees.push({
                        name: labor.employee_name,
                        regular_hours: labor.regular_hours,
                        overtime_hours: labor.overtime_hours,
                        night_shift: labor.night_shift,
                        total: labor.total_amount
                    });
                }
            });
        }
    });

    if (Object.keys(laborTotals).length > 0) {
        lines.push('LABOR BREAKDOWN');
        lines.push('=============================================================');
        lines.push('');

        let laborGrandTotal = 0;

        Object.values(laborTotals).forEach(labor => {
            lines.push(labor.role_name);
            lines.push('-------------------------------------------------------------');

            if (labor.employees.length > 0) {
                lines.push('Employee,Reg Hours,OT Hours,Night Shift,Total');
                labor.employees.forEach(emp => {
                    const regHrs = emp.regular_hours % 1 === 0 ? emp.regular_hours.toFixed(0) : emp.regular_hours.toFixed(2);
                    const otHrs = emp.overtime_hours % 1 === 0 ? emp.overtime_hours.toFixed(0) : emp.overtime_hours.toFixed(2);
                    const nightShiftText = emp.night_shift ? 'Yes' : 'No';
                    lines.push(`"${emp.name}",${regHrs},${otHrs},${nightShiftText},${formatCurrency(emp.total)}`);
                });
            } else {
                lines.push('Description,Reg Hours,OT Hours,Total');
                const regHrs = labor.regular_hours % 1 === 0 ? labor.regular_hours.toFixed(0) : labor.regular_hours.toFixed(2);
                const otHrs = labor.overtime_hours % 1 === 0 ? labor.overtime_hours.toFixed(0) : labor.overtime_hours.toFixed(2);
                lines.push(`${labor.role_name},${regHrs},${otHrs},${formatCurrency(labor.total_amount)}`);
            }

            laborGrandTotal += labor.total_amount;
            lines.push(`${labor.role_name} SUBTOTAL:,,,,${formatCurrency(labor.total_amount)}`);
            lines.push('');
        });

        lines.push('LABOR TOTAL:,,,,${formatCurrency(laborGrandTotal)}');
        lines.push('');
        lines.push('');

        // ========== GRAND TOTAL ==========
        lines.push('=============================================================');
        lines.push('PROJECT TOTALS');
        lines.push('=============================================================');
        lines.push(`Materials Total:,,,,${formatCurrency(materialsGrandTotal)}`);
        lines.push(`Labor Total:,,,,${formatCurrency(laborGrandTotal)}`);
        lines.push('-------------------------------------------------------------');
        lines.push(`GRAND TOTAL:,,,,${formatCurrency(summary.grand_total)}`);
    } else {
        lines.push('=============================================================');
        lines.push(`GRAND TOTAL:,,,,${formatCurrency(summary.grand_total)}`);
    }

    return lines.join('\n');
}

// Download CSV
function downloadCSV(csv, filename) {
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
    document.querySelectorAll('.success-message, .error-message, .info-message').forEach(msg => msg.remove());
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'success' ? 'success-message' : (type === 'error' ? 'error-message' : 'info-message');
    messageDiv.textContent = message;
    const container = document.querySelector('.form-container');
    container.insertBefore(messageDiv, container.firstChild);
    setTimeout(() => messageDiv.remove(), 5000);
}

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
    const { startDate, endDate } = getDateRange();

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
    document.getElementById('inv_start_date').value = startDate || '';
    document.getElementById('inv_end_date').value = endDate || '';

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
document.getElementById('invoiceForm').addEventListener('submit', async function (e) {
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
            showMessage('Invoice generated successfully!', 'success');
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
});

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