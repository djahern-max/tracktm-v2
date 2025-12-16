// TrackTM - Simplified Daily Timesheet Entry Application
const API_BASE = 'http://localhost:8000/api';
window.API_BASE = API_BASE; // Make it globally accessible for invoice.js

let materials = [];
let laborRoles = [];
let currentEntry = null;
let laborRowCounter = 0;
let equipmentRentals = [];

// Helper function to format currency
function formatCurrency(amount) {
    return '$' + amount.toFixed(2);
}

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    // Set today's date as default
    document.getElementById('entryDate').valueAsDate = new Date();

    // Load catalogs
    await loadMaterials();
    await loadLaborRoles();
    await loadEquipmentRentals();

    // Setup event listeners
    document.getElementById('loadBtn').addEventListener('click', loadEntry);
    document.getElementById('newBtn').addEventListener('click', newEntry);
    document.getElementById('saveBtn').addEventListener('click', saveEntry);
    document.getElementById('generatePdfBtn').addEventListener('click', generatePDF);
}

// ============================================
// LOAD CATALOGS
// ============================================

async function loadMaterials() {
    try {
        const response = await fetch(`${API_BASE}/materials`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        materials = data;
        console.log(`Loaded ${materials.length} materials`);
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

async function loadEquipmentRentals() {
    try {
        const response = await fetch(`${API_BASE}/equipment-rentals?year=2022`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        equipmentRentals = data;
        console.log(`Loaded ${equipmentRentals.length} equipment rental items`);
    } catch (error) {
        console.error('Error loading equipment rentals:', error);
        equipmentRentals = [];
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

function newEntry() {
    const jobNumber = document.getElementById('jobNumber').value;
    if (jobNumber) {
        loadJobInfo(jobNumber);
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

    // Materials by category
    const byCategory = {};
    materials.forEach(mat => {
        if (!byCategory[mat.category]) byCategory[mat.category] = [];
        byCategory[mat.category].push(mat);
    });

    Object.entries(byCategory).forEach(([category, items]) => {
        const section = createCategorySection(category, items, existingLineItems);
        container.appendChild(section);
    });

    // Equipment Rentals
    if (equipmentRentals.length > 0) {
        const equipmentSection = createEquipmentRentalSection(existingEquipmentItems);
        container.appendChild(equipmentSection);
    }

    // Labor
    const laborSection = createLaborSection(existingLaborItems);
    container.appendChild(laborSection);

    document.getElementById('actionsBar').style.display = 'flex';

    setupQuantityListeners();
    setupEquipmentListeners();
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
            placeholder="ðŸ” Search materials, equipment, or labor..." 
            class="search-input"
        />
        <button id="clearSearch" class="btn-clear-search">Clear</button>
    `;
    return searchBar;
}

function createCategorySection(category, items, existingLineItems) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = category;
    section.appendChild(header);

    const table = document.createElement('table');
    table.className = 'materials-table';
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

function createEquipmentRentalSection(existingRentalItems = []) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = 'EQUIPMENT RENTALS';
    section.appendChild(header);

    const byCategory = {};
    equipmentRentals.forEach(rental => {
        if (!byCategory[rental.category]) byCategory[rental.category] = [];
        byCategory[rental.category].push(rental);
    });

    Object.entries(byCategory).forEach(([category, items]) => {
        const categoryTable = createEquipmentCategoryTable(category, items, existingRentalItems);
        section.appendChild(categoryTable);
    });

    return section;
}

function createEquipmentCategoryTable(category, items, existingRentalItems) {
    const wrapper = document.createElement('div');
    wrapper.style.marginBottom = '15px';

    const subHeader = document.createElement('div');
    subHeader.style.fontWeight = '600';
    subHeader.style.padding = '8px 0';
    subHeader.style.color = '#6b7280';
    subHeader.textContent = category;
    wrapper.appendChild(subHeader);

    const table = document.createElement('table');
    table.className = 'materials-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th style="width: 45%">Equipment</th>
                <th style="width: 10%">Unit</th>
                <th style="width: 15%">QTY</th>
                <th style="width: 15%">Daily Rate</th>
                <th style="width: 15%; text-align: right;">Total</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');
    items.forEach(item => {
        const existingItem = existingRentalItems.find(ri => ri.equipment_rental_id === item.id);
        const quantity = existingItem ? existingItem.quantity : 0;
        const unitRate = existingItem ? existingItem.unit_rate : item.daily_rate;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="material-name">${item.name}</td>
            <td class="material-unit">${item.unit}</td>
            <td>
                <input 
                    type="number" 
                    class="qty-input equipment-qty-input" 
                    data-equipment-id="${item.id}"
                    value="${quantity > 0 ? quantity : ''}"
                    min="0"
                    step="0.5"
                    placeholder="0"
                />
            </td>
            <td>
                <input 
                    type="number" 
                    class="price-input equipment-rate-input" 
                    data-equipment-id="${item.id}"
                    value="${unitRate || item.daily_rate}"
                    min="0"
                    step="0.01"
                />
            </td>
            <td class="item-total equipment-total" data-equipment-id="${item.id}">
                $${(quantity * (unitRate || item.daily_rate)).toFixed(2)}
            </td>
        `;
        tbody.appendChild(row);
    });

    wrapper.appendChild(table);
    return wrapper;
}

function createLaborSection(existingLaborItems = []) {
    const section = document.createElement('div');
    section.className = 'category-section';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = 'LABOR';
    section.appendChild(header);

    const laborByRole = {};
    existingLaborItems.forEach(item => {
        if (!laborByRole[item.labor_role_id]) laborByRole[item.labor_role_id] = [];
        laborByRole[item.labor_role_id].push(item);
    });

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

    const roleHeader = document.createElement('div');
    roleHeader.className = 'labor-role-header';
    roleHeader.innerHTML = `
        <span class="role-name">${role.name} (${formatCurrency(role.straight_rate)}/hr Reg, ${formatCurrency(role.overtime_rate)}/hr OT)</span>
        <button class="btn-add-employee" data-role-id="${role.id}">+ Add ${role.name}</button>
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
        <button class="btn-remove-employee" data-row-id="${rowId}">Ã—</button>
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
    document.querySelectorAll('.qty-input:not(.equipment-qty-input), .price-input:not(.equipment-rate-input)').forEach(input => {
        input.addEventListener('input', (e) => {
            const materialId = e.target.dataset.materialId;
            updateLineTotal(materialId);
            calculateTotal();
        });
    });
}

function setupEquipmentListeners() {
    document.querySelectorAll('.equipment-qty-input, .equipment-rate-input').forEach(input => {
        input.addEventListener('input', (e) => {
            const equipmentId = e.target.dataset.equipmentId;
            updateEquipmentTotal(equipmentId);
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
        document.querySelectorAll('.category-section > div[style*="marginBottom"]').forEach(wrapper => {
            wrapper.style.display = 'block';
        });
        document.querySelectorAll('.labor-role-section').forEach(section => {
            section.style.display = 'block';
        });
        return;
    }

    document.querySelectorAll('.category-section').forEach(section => {
        let sectionHasVisibleItems = false;

        const subcategoryWrappers = section.querySelectorAll(':scope > div[style*="marginBottom"]');

        if (subcategoryWrappers.length > 0) {
            subcategoryWrappers.forEach(wrapper => {
                let wrapperHasVisibleRows = false;
                const subHeader = wrapper.querySelector('div[style*="fontWeight"]');
                let headerMatches = false;
                if (subHeader) {
                    headerMatches = subHeader.textContent.toLowerCase().includes(term);
                }

                const rows = wrapper.querySelectorAll('.materials-table tbody tr');
                rows.forEach(row => {
                    const nameCell = row.querySelector('.material-name');
                    if (nameCell) {
                        const itemName = nameCell.textContent.toLowerCase();
                        if (itemName.includes(term) || headerMatches) {
                            row.style.display = '';
                            wrapperHasVisibleRows = true;
                            sectionHasVisibleItems = true;
                        } else {
                            row.style.display = 'none';
                        }
                    }
                });

                wrapper.style.display = wrapperHasVisibleRows ? 'block' : 'none';
            });
        } else {
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
        }

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

function updateEquipmentTotal(equipmentId) {
    const qtyInput = document.querySelector(`.equipment-qty-input[data-equipment-id="${equipmentId}"]`);
    const rateInput = document.querySelector(`.equipment-rate-input[data-equipment-id="${equipmentId}"]`);
    const totalCell = document.querySelector(`.equipment-total[data-equipment-id="${equipmentId}"]`);

    const qty = parseFloat(qtyInput.value) || 0;
    const rate = parseFloat(rateInput.value) || 0;
    const total = qty * rate;

    totalCell.textContent = formatCurrency(total);
}

function calculateTotal() {
    let grandTotal = 0;

    // Materials
    document.querySelectorAll('.qty-input:not(.equipment-qty-input)').forEach(input => {
        const materialId = input.dataset.materialId;
        const qty = parseFloat(input.value) || 0;
        const priceInput = document.querySelector(`.price-input[data-material-id="${materialId}"]`);
        const price = parseFloat(priceInput.value) || 0;
        grandTotal += (qty * price);
    });

    // Equipment Rentals
    document.querySelectorAll('.equipment-qty-input').forEach(input => {
        const equipmentId = input.dataset.equipmentId;
        const qty = parseFloat(input.value) || 0;
        const rateInput = document.querySelector(`.equipment-rate-input[data-equipment-id="${equipmentId}"]`);
        const rate = parseFloat(rateInput.value) || 0;
        grandTotal += (qty * rate);
    });

    // Labor - Fixed to properly parse the text content
    document.querySelectorAll('.labor-total').forEach(cell => {
        const totalText = cell.textContent.trim();
        // Remove $, commas, and any other non-numeric characters except decimal point
        const cleanText = totalText.replace(/[$,]/g, '');
        const total = parseFloat(cleanText) || 0;
        console.log('Labor total found:', totalText, 'â†’ parsed as:', total);
        grandTotal += total;
    });

    console.log('Grand total calculated:', grandTotal);
    document.getElementById('dailyTotal').textContent = formatCurrency(grandTotal);
}

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
    document.querySelectorAll('.qty-input:not(.equipment-qty-input)').forEach(input => {
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

    // Collect equipment rental items
    const equipmentItems = [];
    document.querySelectorAll('.equipment-qty-input').forEach(input => {
        const qty = parseFloat(input.value) || 0;
        if (qty > 0) {
            const equipmentId = parseInt(input.dataset.equipmentId);
            const rateInput = document.querySelector(`.equipment-rate-input[data-equipment-id="${equipmentId}"]`);
            const unitRate = parseFloat(rateInput.value);

            equipmentItems.push({
                equipment_rental_id: equipmentId,
                quantity: qty,
                unit_rate: unitRate,
                rate_period: "daily"
            });
        }
    });

    // Collect labor items
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

    if (lineItems.length === 0 && laborItems.length === 0 && equipmentItems.length === 0) {
        alert('Please enter at least one material quantity, equipment, or labor hours');
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
                labor_items: laborItems
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

// ============================================
// UTILITY FUNCTIONS
// ============================================

function saveJobInfo(jobNumber, companyName, jobName) {
    if (!jobNumber) return;
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