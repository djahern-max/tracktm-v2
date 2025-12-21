// employees.js - Employee Management Module
// Handles employee selection, hour entry, and calculations

(function () {
    'use strict';

    let employees = [];
    let employeeRowCounter = 0;

    // ============================================
    // INITIALIZATION
    // ============================================

    async function initEmployees() {
        console.log('Initializing employees module...');
        await loadEmployees();
        console.log(`Loaded ${employees.length} employees`);
    }

    // ============================================
    // LOAD EMPLOYEES
    // ============================================

    async function loadEmployees() {
        try {
            const response = await fetch(`${window.API_BASE}/employees?active_only=true`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            employees = data;
        } catch (error) {
            console.error('Error loading employees:', error);
            alert('Failed to load employees: ' + error.message);
            employees = [];
        }
    }

    // ============================================
    // CREATE EMPLOYEES SECTION
    // ============================================

    function createEmployeesSection(existingEmployeeEntries = []) {
        const section = document.createElement('div');
        section.className = 'category-section';
        section.id = 'employees-section';

        const header = document.createElement('div');
        header.className = 'category-header';
        header.textContent = 'BURDENED RATE LABOR';
        section.appendChild(header);

        // Employee selector and container
        const selectorContainer = document.createElement('div');
        selectorContainer.className = 'employee-selector-container';
        selectorContainer.style.padding = '15px';
        selectorContainer.style.background = '#f9fafb';
        selectorContainer.style.borderBottom = '1px solid #e5e7eb';

        // Create dropdown
        const select = createEmployeeDropdown();
        const addButton = document.createElement('button');
        addButton.className = 'btn-add-employee-main';
        addButton.textContent = '+ Add Employee';
        addButton.style.marginLeft = '10px';
        addButton.disabled = true;

        // Layout for selector
        const selectorRow = document.createElement('div');
        selectorRow.style.display = 'flex';
        selectorRow.style.gap = '10px';
        selectorRow.style.alignItems = 'center';
        selectorRow.appendChild(select);
        selectorRow.appendChild(addButton);
        selectorContainer.appendChild(selectorRow);

        section.appendChild(selectorContainer);

        // Container for employee rows
        const employeesContainer = document.createElement('div');
        employeesContainer.className = 'employees-entries-container';
        employeesContainer.id = 'employees-entries-container';
        employeesContainer.style.padding = '15px';

        if (existingEmployeeEntries.length === 0) {
            employeesContainer.innerHTML = '<div class="empty-state">No employees added. Select an employee above and click "Add Employee".</div>';
        } else {
            existingEmployeeEntries.forEach(entry => {
                const row = createEmployeeEntryRow(entry);
                employeesContainer.appendChild(row);
            });

            setTimeout(() => {
                if (window.calculateTotal) window.calculateTotal();
            }, 100);
        }

        section.appendChild(employeesContainer);

        // Event listeners
        select.addEventListener('change', () => {
            addButton.disabled = !select.value;
        });

        addButton.addEventListener('click', () => {
            const employeeId = parseInt(select.value);
            if (employeeId) {
                addEmployeeEntry(employeeId);
                select.value = '';
                addButton.disabled = true;
            }
        });

        return section;
    }

    // ============================================
    // CREATE EMPLOYEE DROPDOWN
    // ============================================

    function createEmployeeDropdown() {
        const select = document.createElement('select');
        select.className = 'employee-dropdown';
        select.style.flex = '1';
        select.style.padding = '8px 12px';
        select.style.border = '1px solid #d1d5db';
        select.style.borderRadius = '6px';
        select.style.fontSize = '1rem';

        // Add empty option
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = 'Select Employee...';
        select.appendChild(emptyOption);

        // Group employees by union
        const byUnion = {};
        employees.forEach(emp => {
            if (!byUnion[emp.union]) byUnion[emp.union] = [];
            byUnion[emp.union].push(emp);
        });

        // Sort unions
        const sortedUnions = Object.keys(byUnion).sort();

        // Add optgroups for each union
        sortedUnions.forEach(union => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = union;

            // Sort employees by last name
            const sortedEmployees = byUnion[union].sort((a, b) =>
                a.last_name.localeCompare(b.last_name)
            );

            sortedEmployees.forEach(emp => {
                const option = document.createElement('option');
                option.value = emp.id;
                option.textContent = `${emp.full_name} (#${emp.employee_number})`;
                optgroup.appendChild(option);
            });

            select.appendChild(optgroup);
        });

        return select;
    }

    // ============================================
    // ADD EMPLOYEE ENTRY
    // ============================================

    function addEmployeeEntry(employeeId) {
        const employee = employees.find(e => e.id === employeeId);
        if (!employee) {
            console.error(`Employee ID ${employeeId} not found`);
            return;
        }

        const container = document.getElementById('employees-entries-container');

        // Remove empty state if present
        const emptyState = container.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        // Create employee entry with default 0 hours
        const entryData = {
            employee_id: employee.id,
            employee: employee,
            regular_hours: 0,
            overtime_hours: 0,
            night_shift: false
        };

        const row = createEmployeeEntryRow(entryData);
        container.appendChild(row);

        // Trigger calculation
        updateEmployeeEntryTotal(row.dataset.rowId);
        if (window.calculateTotal) window.calculateTotal();
    }

    // ============================================
    // CREATE EMPLOYEE ENTRY ROW
    // ============================================

    function createEmployeeEntryRow(entryData) {
        employeeRowCounter++;
        const rowId = `employee-entry-${employeeRowCounter}`;

        const row = document.createElement('div');
        row.className = 'employee-entry-row';
        row.dataset.rowId = rowId;
        row.dataset.employeeId = entryData.employee_id || entryData.employee?.id;

        // Get employee data
        const employee = entryData.employee || employees.find(e => e.id === entryData.employee_id);

        if (!employee) {
            console.error('Employee not found for entry:', entryData);
            return row;
        }

        const regHours = entryData.regular_hours || 0;
        const otHours = entryData.overtime_hours || 0;
        const nightShift = entryData.night_shift || false;

        row.innerHTML = `
        <div class="employee-entry-header">
            <div class="employee-info">
                <strong>${employee.full_name}</strong>
                <span class="employee-meta">#${employee.employee_number} ${employee.union}</span>
            </div>
            <button class="btn-remove-employee-entry" data-row-id="${rowId}">&times;</button>
        </div>
        <div class="employee-entry-details">
            <div class="employee-rates">
                <span class="rate-badge">Reg: $${employee.regular_rate}/hr</span>
                <span class="rate-badge">OT: $${employee.overtime_rate}/hr</span>
                <span class="rate-badge">H&W: $${employee.health_welfare}/hr</span>
                <span class="rate-badge">Pension: $${employee.pension}/hr</span>
            </div>
        </div>
        <div class="employee-entry-inputs">
            <div class="input-group">
                <label>Regular Hours</label>
                <input 
                    type="number" 
                    class="employee-reg-input" 
                    data-row-id="${rowId}"
                    value="${regHours > 0 ? regHours : ''}"
                    min="0"
                    step="0.5"
                    placeholder="0"
                />
            </div>
            <div class="input-group">
                <label>Overtime Hours</label>
                <input 
                    type="number" 
                    class="employee-ot-input" 
                    data-row-id="${rowId}"
                    value="${otHours > 0 ? otHours : ''}"
                    min="0"
                    step="0.5"
                    placeholder="0"
                />
            </div>
            <div class="input-group">
                <label class="night-shift-label">
                    <input 
                        type="checkbox" 
                        class="employee-night-shift" 
                        data-row-id="${rowId}"
                        ${nightShift ? 'checked' : ''}
                    />
                    <span>Night Shift (+$2/hr)</span>
                </label>
            </div>
            <div class="input-group total-group">
                <label>Total Cost</label>
                <div class="employee-entry-total" data-row-id="${rowId}">$0.00</div>
            </div>
        </div>
    `;

        // Add event listeners
        const regInput = row.querySelector('.employee-reg-input');
        const otInput = row.querySelector('.employee-ot-input');
        const nightCheckbox = row.querySelector('.employee-night-shift');
        const removeBtn = row.querySelector('.btn-remove-employee-entry');

        [regInput, otInput, nightCheckbox].forEach(input => {
            input.addEventListener('input', () => {
                updateEmployeeEntryTotal(rowId);
                if (window.calculateTotal) window.calculateTotal();
            });
        });

        removeBtn.addEventListener('click', () => {
            row.remove();

            // Show empty state if no more entries
            const container = document.getElementById('employees-entries-container');
            if (container.children.length === 0) {
                container.innerHTML = '<div class="empty-state">No employees added. Select an employee above and click "Add Employee".</div>';
            }

            if (window.calculateTotal) window.calculateTotal();
        });

        // Calculate initial total
        setTimeout(() => updateEmployeeEntryTotal(rowId), 0);

        return row;
    }

    // ============================================
    // UPDATE EMPLOYEE ENTRY TOTAL
    // ============================================

    function updateEmployeeEntryTotal(rowId) {
        const row = document.querySelector(`.employee-entry-row[data-row-id="${rowId}"]`);
        if (!row) return;

        const employeeId = parseInt(row.dataset.employeeId);
        const employee = employees.find(e => e.id === employeeId);
        if (!employee) return;

        const regInput = row.querySelector('.employee-reg-input');
        const otInput = row.querySelector('.employee-ot-input');
        const nightCheckbox = row.querySelector('.employee-night-shift');
        const totalCell = row.querySelector('.employee-entry-total');

        const regHours = parseFloat(regInput.value) || 0;
        const otHours = parseFloat(otInput.value) || 0;
        const nightShift = nightCheckbox.checked;
        const totalHours = regHours + otHours;

        // Calculate base wages
        let regRate = employee.regular_rate;
        let otRate = employee.overtime_rate;

        if (nightShift) {
            regRate += 2.00;
            otRate += 2.00;
        }

        const wagesCost = (regHours * regRate) + (otHours * otRate);

        // Calculate benefits (applied to all hours)
        const hwCost = totalHours * employee.health_welfare;
        const pensionCost = totalHours * employee.pension;

        const totalCost = wagesCost + hwCost + pensionCost;

        totalCell.textContent = `$${totalCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    // ============================================
    // COLLECT EMPLOYEE ENTRIES FOR SAVE
    // ============================================

    function collectEmployeeEntries() {
        const employeeItems = [];

        document.querySelectorAll('.employee-entry-row').forEach(row => {
            const rowId = row.dataset.rowId;
            const employeeId = parseInt(row.dataset.employeeId);

            const regInput = row.querySelector('.employee-reg-input');
            const otInput = row.querySelector('.employee-ot-input');
            const nightCheckbox = row.querySelector('.employee-night-shift');

            const regHours = parseFloat(regInput.value) || 0;
            const otHours = parseFloat(otInput.value) || 0;

            if (regHours > 0 || otHours > 0) {
                employeeItems.push({
                    labor_role_id: 1,
                    employee_id: employeeId,
                    regular_hours: regHours,
                    overtime_hours: otHours,
                    night_shift: nightCheckbox.checked
                });
            }
        });

        return employeeItems;
    }

    // ============================================
    // CALCULATE EMPLOYEE TOTAL FOR GRAND TOTAL
    // ============================================

    function calculateEmployeeTotal() {
        let total = 0;

        document.querySelectorAll('.employee-entry-total').forEach(cell => {
            const totalText = cell.textContent.trim();
            const cleanText = totalText.replace(/[$,]/g, '');
            const amount = parseFloat(cleanText) || 0;
            total += amount;
        });

        return total;
    }

    // ============================================
    // EXPORT FOR GLOBAL ACCESS
    // ============================================

    window.EmployeesModule = {
        init: initEmployees,
        createSection: createEmployeesSection,
        collectEntries: collectEmployeeEntries,
        calculateTotal: calculateEmployeeTotal
    };

}());