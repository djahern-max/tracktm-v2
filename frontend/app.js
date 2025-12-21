// TrackTM - Simplified Daily Timesheet Entry Application
const API_BASE = 'http://localhost:8000/api';
window.API_BASE = API_BASE; // Make it globally accessible for invoice.js

let materials = [];
let laborRoles = [];
let currentEntry = null;
let laborRowCounter = 0;
let jobEquipment = [];

// Helper function to format currency
function formatCurrency(amount) {
    return '$' + amount.toFixed(2);
}

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    // Set today's date as default
    document.getElementById('entryDate').valueAsDate = new Date();

    // Load last used job number from localStorage
    const lastJobNumber = localStorage.getItem('tracktm_last_job_number');
    if (lastJobNumber) {
        document.getElementById('jobNumber').value = lastJobNumber;
    }

    // Load catalogs
    await loadMaterials();
    await loadLaborRoles();

    // Load employees if module is available
    if (window.EmployeesModule && window.EmployeesModule.init) {
        await window.EmployeesModule.init();
    }

    // Setup event listeners
    document.getElementById('loadBtn').addEventListener('click', loadEntry);
    document.getElementById('newBtn').addEventListener('click', newEntry);
    document.getElementById('saveBtn').addEventListener('click', saveEntry);
    document.getElementById('generatePdfBtn').addEventListener('click', generatePDF);
    document.getElementById('generateUnionReportsBtn').addEventListener('click', generateUnionReports);

    // Con9 CSV button (may not exist in older HTML)
    const con9CsvBtn = document.getElementById('generateCon9CsvBtn');
    if (con9CsvBtn) {
        con9CsvBtn.addEventListener('click', generateCon9CSV);
    }
}

// ============================================
// LOAD CATALOGS
// ============================================

async function loadMaterials() {
    try {
        const jobNumber = document.getElementById('jobNumber').value;
        const url = jobNumber
            ? `${API_BASE}/materials?job_number=${jobNumber}`
            : `${API_BASE}/materials`;

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        materials = data;
        console.log(`Loaded ${materials.length} materials${jobNumber ? ` for job ${jobNumber}` : ''}`);
    } catch (error) {
        console.error('Error loading materials:', error);
        alert('Failed to load materials catalog');
    }
}

async function loadLaborRoles() {
    try {
        const response = await fetch(`${API_BASE}/labor-roles`);
        const data = await response.json();
        laborRoles = data;
        console.log(`Loaded ${laborRoles.length} labor roles`);
    } catch (error) {
        console.error('Error loading labor roles:', error);
        alert('Failed to load labor roles');
    }
}

async function loadJobEquipment(jobNumber) {
    if (!jobNumber) {
        jobEquipment = [];
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/job-equipment/${jobNumber}`);
        if (!response.ok) {
            console.log(`No job-specific equipment for job ${jobNumber}`);
            jobEquipment = [];
            return;
        }
        const data = await response.json();
        jobEquipment = data;
        console.log(`Ã¢Å“â€œ Loaded ${jobEquipment.length} equipment items for job ${jobNumber}`);
    } catch (error) {
        console.error('Error loading job equipment:', error);
        jobEquipment = [];
    }
}

// ============================================
// LOAD/CREATE ENTRY
// ============================================

async function loadEntry() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;

    if (!jobNumber || !entryDate) {
        alert('Please enter job number and date');
        return;
    }

    loadJobInfo(jobNumber);

    // Reload catalogs for this job
    await loadMaterials();
    await loadJobEquipment(jobNumber);

    try {
        const response = await fetch(`${API_BASE}/entries/${jobNumber}/${entryDate}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        if (data.entry) {
            currentEntry = data.entry;
            displayForm(
                currentEntry.line_items,
                currentEntry.labor_entries || [],
                currentEntry.equipment_rental_items || []
            );
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

async function newEntry() {
    const jobNumber = document.getElementById('jobNumber').value;
    if (jobNumber) {
        loadJobInfo(jobNumber);
        // Reload catalogs for this job
        await loadMaterials();
        await loadJobEquipment(jobNumber);
    }
    currentEntry = null;
    displayForm([], [], []);
    document.getElementById('actionsBar').style.display = 'flex';
}

// ============================================
// DISPLAY FORM
// ============================================

function displayForm(existingLineItems = [], existingLaborItems = [], existingEquipmentItems = []) {
    const container = document.getElementById('formContainer');
    container.innerHTML = '';
    laborRowCounter = 0;

    // Search bar
    const searchBar = createSearchBar();
    container.appendChild(searchBar);

    // Single Materials Section - alphabetically sorted
    const materialsSection = createMaterialsSection(existingLineItems);
    container.appendChild(materialsSection);

    // Simplified Equipment Section (if equipment exists for this job)
    if (jobEquipment.length > 0) {
        const equipmentSection = createSimplifiedEquipmentSection(existingEquipmentItems);
        container.appendChild(equipmentSection);
    }

    // Fixed Rate Labor - ONLY entries WITHOUT employee_id
    const fixedRateLaborItems = existingLaborItems.filter(item => !item.employee_id);
    const laborSection = createLaborSection(fixedRateLaborItems);
    container.appendChild(laborSection);

    // Burdened Rate Labor (Employees) - ONLY entries WITH employee_id
    const employeeEntries = existingLaborItems.filter(item => item.employee_id);
    const employeesSection = window.EmployeesModule.createSection(employeeEntries);
    container.appendChild(employeesSection);

    document.getElementById('actionsBar').style.display = 'flex';

    setupQuantityListeners();
    setupSimplifiedEquipmentListeners();
    setupSearchListeners();
    calculateTotal();
}

// ============================================
// CREATE SECTIONS
// ============================================

function createSearchBar() {
    const searchBar = document.createElement('div');
    searchBar.className = 'search-bar';
    searchBar.innerHTML = `
        <input 
            type="text" 
            id="itemSearch" 
            placeholder="Search materials, equipment, or labor..." 
            class="search-input"
        />
        <button id="clearSearch" class="btn-clear-search">Clear</button>
    `;
    return searchBar;
}

function createMaterialsSection(existingLineItems = []) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = 'MATERIALS';
    section.appendChild(header);

    // Sort materials alphabetically by name
    const sortedMaterials = [...materials].sort((a, b) =>
        a.name.localeCompare(b.name)
    );

    const table = document.createElement('table');
    table.className = 'materials-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th style="width: 50%">Description</th>
                <th style="width: 15%">QTY</th>
                <th style="width: 15%">Price</th>
                <th style="width: 20%; text-align: right;">Total</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');
    sortedMaterials.forEach(item => {
        const existingItem = existingLineItems.find(li => li.material_id === item.id);
        const quantity = existingItem ? existingItem.quantity : 0;
        const unitPrice = existingItem ? existingItem.unit_price : item.unit_price;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="material-name">${item.name}</td>
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
                    value="${parseFloat(unitPrice).toFixed(2)}"
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

function createSimplifiedEquipmentSection(existingEquipmentItems = []) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = 'EQUIPMENT';
    section.appendChild(header);

    // Sort equipment alphabetically
    const sortedEquipment = [...jobEquipment].sort((a, b) =>
        a.name.localeCompare(b.name)
    );

    const table = document.createElement('table');
    table.className = 'materials-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th style="width: 40%">Equipment</th>
                <th style="width: 12%">Pieces</th>
                <th style="width: 12%">Hours</th>
                <th style="width: 16%">Hourly Rate</th>
                <th style="width: 20%; text-align: right;">Total</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');
    sortedEquipment.forEach(item => {
        // Find existing entry by matching equipment name
        const existingItem = existingEquipmentItems.find(ei =>
            ei.equipment_name === item.name
        );

        // Ã¢Å“â€¦ FIX: Default pieces to 1 if not specified
        const pieces = (existingItem && existingItem.pieces) ? existingItem.pieces : 1;
        const hours = existingItem ? existingItem.quantity : 0;
        const hourlyRate = item.hourly_rate;

        // Ã¢Å“â€¦ FIX: Calculate initial total properly
        const initialTotal = pieces * hours * hourlyRate;

        const row = document.createElement('tr');
        row.innerHTML = `
        <td class="material-name">${item.name}</td>
        <td>
            <input 
                type="number" 
                class="equipment-pieces-input" 
                data-equipment-id="${item.id}"
                data-equipment-name="${item.name}"
                value="${pieces}"
                min="1"
                step="1"
                placeholder="1"
            />
        </td>
        <td>
            <input 
                type="number" 
                class="equipment-hours-input" 
                data-equipment-id="${item.id}"
                data-equipment-name="${item.name}"
                data-hourly-rate="${parseFloat(hourlyRate).toFixed(2)}"
                value="${hours > 0 ? hours : ''}"
                min="0"
                step="0.5"
                placeholder="0"
            />
        </td>
        <td class="equipment-rate-display">
            $${parseFloat(hourlyRate).toFixed(2)}
        </td>
        <td class="equipment-total" data-equipment-id="${item.id}">
            $${initialTotal.toFixed(2)}
        </td>
    `;
        tbody.appendChild(row);
    });

    section.appendChild(table);
    return section;
}

function createLaborSection(existingLaborItems = []) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header collapsible-header';
    header.innerHTML = `
        <span>FIXED RATE LABOR</span>
        <span class="collapse-icon">Ã¢â€“Â¶</span>
    `;
    header.style.cursor = 'pointer';
    section.appendChild(header);

    // Container for all labor role sections (collapsible content)
    const laborContent = document.createElement('div');
    laborContent.className = 'collapsible-content';
    laborContent.style.display = 'none'; // Start collapsed

    // Add helper text
    const helperText = document.createElement('div');
    helperText.style.padding = '12px 15px';
    helperText.style.background = '#eff6ff';
    helperText.style.border = '1px solid #bfdbfe';
    helperText.style.borderRadius = '6px';
    helperText.style.margin = '10px';
    helperText.style.fontSize = '0.875rem';
    helperText.style.color = '#1e40af';
    helperText.innerHTML = `
        <strong>Note:</strong> For actual employees with payroll rates, use the 
        <strong>BURDENED RATE LABOR</strong> section below. This section is for 
        simple hourly rate entries only.
    `;
    laborContent.appendChild(helperText);

    const laborByRole = {};
    existingLaborItems.forEach(item => {
        if (!laborByRole[item.labor_role_id]) laborByRole[item.labor_role_id] = [];
        laborByRole[item.labor_role_id].push(item);
    });

    laborRoles.forEach(role => {
        const roleSection = createLaborRoleSection(role, laborByRole[role.id] || []);
        laborContent.appendChild(roleSection);
    });

    section.appendChild(laborContent);

    // Add click handler to toggle
    header.addEventListener('click', () => {
        const icon = header.querySelector('.collapse-icon');
        if (laborContent.style.display === 'none') {
            laborContent.style.display = 'block';
            icon.textContent = 'Ã¢â€“Â¼';
        } else {
            laborContent.style.display = 'none';
            icon.textContent = 'Ã¢â€“Â¶';
        }
    });

    return section;
}

function createLaborRoleSection(role, existingEmployees = []) {
    const roleSection = document.createElement('div');
    roleSection.className = 'labor-role-section';
    roleSection.setAttribute('data-role-id', role.id);

    // Abbreviate role names for uniform button sizes
    const roleAbbreviations = {
        'Painter': 'Painter',
        'Supervisor': 'Supervisor',
        'Project Manager': 'Manager',
        'Per Diem': 'Per Diem'
    };
    const buttonText = roleAbbreviations[role.name] || role.name;

    const roleHeader = document.createElement('div');
    roleHeader.className = 'labor-role-header';
    roleHeader.innerHTML = `
        <span class="role-name">${role.name} (${formatCurrency(role.straight_rate)}/hr Reg, ${formatCurrency(role.overtime_rate)}/hr OT)</span>
        <button class="btn-add-employee" data-role-id="${role.id}">+ Add ${buttonText}</button>
    `;
    roleSection.appendChild(roleHeader);

    const employeesContainer = document.createElement('div');
    employeesContainer.className = 'employees-container';
    employeesContainer.setAttribute('data-role-id', role.id);

    if (existingEmployees.length > 0) {
        existingEmployees.forEach(emp => {
            const row = createEmployeeRow(role, emp);
            employeesContainer.appendChild(row);
        });
    } else {
        employeesContainer.innerHTML = '<div class="empty-state">No employees added. Click "+ Add" to add an employee.</div>';
    }

    roleSection.appendChild(employeesContainer);

    roleHeader.querySelector('.btn-add-employee').addEventListener('click', () => {
        addEmployeeRow(role);
    });

    return roleSection;
}

function addEmployeeRow(role) {
    const container = document.querySelector(`.employees-container[data-role-id="${role.id}"]`);
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

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
        <button class="btn-remove-employee" data-row-id="${rowId}">&times;</button>
    `;

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

    employeeInput.addEventListener('blur', () => {
        if (employeeInput.value) {
            saveEmployeeName(role.id, employeeInput.value);
        }
    });

    row.querySelector('.btn-remove-employee').addEventListener('click', () => {
        row.remove();
        const container = document.querySelector(`.employees-container[data-role-id="${role.id}"]`);
        if (container.children.length === 0) {
            container.innerHTML = '<div class="empty-state">No employees added. Click "+ Add" to add an employee.</div>';
        }
        calculateTotal();
    });

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

// ============================================
// LISTENERS
// ============================================

function setupQuantityListeners() {
    document.querySelectorAll('.qty-input, .price-input').forEach(input => {
        input.addEventListener('input', (e) => {
            const materialId = e.target.dataset.materialId;
            updateLineTotal(materialId);
            calculateTotal();
        });
    });
}

function setupSimplifiedEquipmentListeners() {
    document.querySelectorAll('.equipment-hours-input, .equipment-pieces-input').forEach(input => {
        input.addEventListener('input', (e) => {
            const equipmentId = e.target.dataset.equipmentId;

            // Get both pieces and hours
            const piecesInput = document.querySelector(`.equipment-pieces-input[data-equipment-id="${equipmentId}"]`);
            const hoursInput = document.querySelector(`.equipment-hours-input[data-equipment-id="${equipmentId}"]`);

            // Ã¢Å“â€¦ FIX: Use 1 as default for pieces, handle empty/NaN properly
            const piecesValue = parseFloat(piecesInput.value);
            const pieces = (isNaN(piecesValue) || piecesValue < 1) ? 1 : piecesValue;

            const hours = parseFloat(hoursInput.value) || 0;
            const hourlyRate = parseFloat(hoursInput.dataset.hourlyRate) || 0;

            const total = pieces * hours * hourlyRate;

            const totalCell = document.querySelector(`.equipment-total[data-equipment-id="${equipmentId}"]`);
            if (totalCell) {
                totalCell.textContent = `$${total.toFixed(2)}`;
            }

            calculateTotal();
        });
    });
}
function setupSearchListeners() {
    const searchInput = document.getElementById('itemSearch');
    const clearBtn = document.getElementById('clearSearch');

    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterItems(e.target.value);
            }, 300);
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                filterItems('');
                searchInput.focus();
            });
        }
    }
}

function filterItems(searchTerm) {
    const term = searchTerm.toLowerCase().trim();

    if (!term) {
        document.querySelectorAll('.category-section').forEach(section => {
            section.style.display = 'block';
        });
        document.querySelectorAll('.materials-table tbody tr').forEach(row => {
            row.style.display = '';
        });
        document.querySelectorAll('.labor-role-section').forEach(section => {
            section.style.display = 'block';
        });
        return;
    }

    document.querySelectorAll('.category-section').forEach(section => {
        let sectionHasVisibleItems = false;

        const rows = section.querySelectorAll('.materials-table tbody tr');
        rows.forEach(row => {
            const nameCell = row.querySelector('.material-name');
            if (nameCell) {
                const itemName = nameCell.textContent.toLowerCase();
                if (itemName.includes(term)) {
                    row.style.display = '';
                    sectionHasVisibleItems = true;
                } else {
                    row.style.display = 'none';
                }
            }
        });

        section.style.display = sectionHasVisibleItems ? 'block' : 'none';
    });

    document.querySelectorAll('.labor-role-section').forEach(section => {
        const roleNameEl = section.querySelector('.role-name');
        if (roleNameEl) {
            const roleName = roleNameEl.textContent.toLowerCase();
            if (roleName.includes(term)) {
                section.style.display = 'block';
            } else {
                section.style.display = 'none';
            }
        }
    });
}

// ============================================
// CALCULATIONS
// ============================================

function updateLineTotal(materialId) {
    const qtyInput = document.querySelector(`.qty-input[data-material-id="${materialId}"]`);
    const priceInput = document.querySelector(`.price-input[data-material-id="${materialId}"]`);
    const totalCell = document.querySelector(`.item-total[data-material-id="${materialId}"]`);

    const qty = parseFloat(qtyInput.value) || 0;
    const price = parseFloat(priceInput.value) || 0;
    const total = qty * price;

    totalCell.textContent = formatCurrency(total);
}

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

    // Equipment
    document.querySelectorAll('.equipment-total').forEach(cell => {
        const totalText = cell.textContent.trim();
        const cleanText = totalText.replace(/[$,]/g, '');
        const total = parseFloat(cleanText) || 0;
        grandTotal += total;
    });

    // Fixed Rate Labor
    document.querySelectorAll('.labor-total').forEach(cell => {
        const totalText = cell.textContent.trim();
        const cleanText = totalText.replace(/[$,]/g, '');
        const total = parseFloat(cleanText) || 0;
        grandTotal += total;
    });

    // Burdened Rate Labor (Employees)
    const employeeTotal = window.EmployeesModule.calculateTotal();
    grandTotal += employeeTotal;

    document.getElementById('dailyTotal').textContent = formatCurrency(grandTotal);
}

window.calculateTotal = calculateTotal;

// ============================================
// SAVE ENTRY
// ============================================

async function saveEntry() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;
    const companyName = document.getElementById('companyName').value;
    const jobName = document.getElementById('jobName').value;

    if (!jobNumber || !entryDate) {
        alert('Please enter job number and date');
        return;
    }

    saveJobInfo(jobNumber, companyName, jobName);

    // Collect line items (materials)
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

    // Collect equipment items
    const equipmentItems = [];
    document.querySelectorAll('.equipment-hours-input').forEach(input => {
        const hours = parseFloat(input.value) || 0;
        if (hours > 0) {
            const equipmentName = input.dataset.equipmentName;
            const hourlyRate = parseFloat(input.dataset.hourlyRate);

            equipmentItems.push({
                equipment_rental_id: 0, // Placeholder for job equipment
                quantity: hours,
                unit_rate: hourlyRate,
                rate_period: "hourly",
                equipment_name: equipmentName  // Send the equipment name
            });
        }
    });

    // Collect labor items (generic labor section)
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

    // Collect employee entries
    const employeeItems = window.EmployeesModule.collectEntries();

    // Combine all labor items
    const allLaborItems = [...laborItems, ...employeeItems];

    if (lineItems.length === 0 && allLaborItems.length === 0 && equipmentItems.length === 0) {
        alert('Please enter at least one material quantity, equipment hours, or labor hours');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_number: jobNumber,
                entry_date: entryDate,
                line_items: lineItems,
                equipment_items: equipmentItems,
                labor_items: allLaborItems
            })
        });

        const data = await response.json();

        if (response.ok) {
            const materialsTotal = data.entry.line_items.reduce((sum, item) => sum + item.total_amount, 0);
            const equipmentTotal = data.entry.equipment_rental_items ?
                data.entry.equipment_rental_items.reduce((sum, item) => sum + item.total_amount, 0) : 0;
            const laborTotal = data.entry.labor_entries.reduce((sum, item) => sum + item.total_amount, 0);
            const grandTotal = materialsTotal + equipmentTotal + laborTotal;
            showMessage(`Entry saved successfully! Total: ${formatCurrency(grandTotal)}`, 'success');
            currentEntry = data.entry;
        } else {
            alert('Failed to save entry: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving entry:', error);
        alert('Failed to save entry: ' + error.message);
    }
}

// ============================================
// GENERATE PDF
// ============================================

async function generatePDF() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;
    const companyName = document.getElementById('companyName').value || 'Tri-State Painting, LLC (TSI)';
    const jobName = document.getElementById('jobName').value || '';

    if (!jobNumber || !entryDate) {
        alert('Please load an entry first');
        return;
    }

    const formData = {
        job_number: jobNumber,
        job_name: jobName,
        company_name: companyName,
        company_address_line1: '612 West Main Street Unit 2',
        company_address_line2: 'Tilton, NH 03276',
        company_phone: '(603) 286-7657',
        company_fax: '(603) 286-7882',
        start_date: entryDate
    };

    try {
        showMessage('Generating PDF...', 'info');

        const response = await fetch(`${API_BASE}/reports/daily`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `TSI_Report_${jobNumber}_${entryDate}.pdf`;

            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showMessage('PDF generated successfully!', 'success');
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Unknown error');
        }
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert('Failed to generate PDF: ' + error.message);
    }
}

async function generateCon9CSV() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;
    const companyName = document.getElementById('companyName').value || 'Tri-State Painting, LLC (TSI)';
    const jobName = document.getElementById('jobName').value || '';

    if (!jobNumber || !entryDate) {
        alert('Please load an entry first');
        return;
    }

    const formData = {
        job_number: jobNumber,
        job_name: jobName,
        company_name: companyName,
        company_address_line1: '612 West Main Street Unit 2',
        company_address_line2: 'Tilton, NH 03276',
        company_phone: '(603) 286-7657',
        company_fax: '(603) 286-7882',
        start_date: entryDate
    };

    try {
        showMessage('Generating Con9 CSV...', 'info');

        const response = await fetch(`${API_BASE}/reports/con9-csv`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Con9_${jobNumber}_${entryDate}.csv`;

            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showMessage('Con9 CSV exported successfully!', 'success');
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Unknown error');
        }
    } catch (error) {
        console.error('Error generating Con9 CSV:', error);
        alert('Failed to generate Con9 CSV: ' + error.message);
    }
}


async function generateUnionReports() {
    const jobNumber = document.getElementById('jobNumber').value;
    const entryDate = document.getElementById('entryDate').value;
    const companyName = document.getElementById('companyName').value || 'Tri-State Painting, LLC (TSI)';
    const jobName = document.getElementById('jobName').value || '';

    if (!jobNumber || !entryDate) {
        alert('Please load an entry first');
        return;
    }

    const formData = {
        job_number: jobNumber,
        job_name: jobName,
        company_name: companyName,
        company_address_line1: '612 West Main Street Unit 2',
        company_address_line2: 'Tilton, NH 03276',
        company_phone: '(603) 286-7657',
        company_fax: '(603) 286-7882',
        start_date: entryDate
    };

    try {
        showMessage('Generating union reports...', 'info');

        const response = await fetch(`${API_BASE}/reports/union-reports`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `JFW_LABOR_REPORTS_${jobNumber}_${entryDate}.zip`; // Ã¢Å“â€¦ CHANGED TO .zip

            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showMessage('Union reports generated successfully!', 'success');
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Unknown error');
        }
    } catch (error) {
        console.error('Error generating union reports:', error);
        alert('Failed to generate union reports: ' + error.message);
    }
}
// ============================================
// UTILITY FUNCTIONS
// ============================================

function saveJobInfo(jobNumber, companyName, jobName) {
    if (!jobNumber) return;
    localStorage.setItem('tracktm_last_job_number', jobNumber); // Remember last used job
    const jobInfo = { companyName, jobName };
    localStorage.setItem(`tracktm_job_${jobNumber}`, JSON.stringify(jobInfo));
}

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

function saveEmployeeName(laborRoleId, employeeName) {
    localStorage.setItem(`tracktm_labor_${laborRoleId}`, employeeName);
}

function loadEmployeeName(laborRoleId) {
    return localStorage.getItem(`tracktm_labor_${laborRoleId}`) || '';
}

function showMessage(message, type = 'info') {
    document.querySelectorAll('.success-message, .error-message, .info-message').forEach(msg => msg.remove());
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'success' ? 'success-message' : (type === 'error' ? 'error-message' : 'info-message');
    messageDiv.textContent = message;
    const container = document.querySelector('.form-container');
    container.insertBefore(messageDiv, container.firstChild);
    setTimeout(() => messageDiv.remove(), 5000);
}