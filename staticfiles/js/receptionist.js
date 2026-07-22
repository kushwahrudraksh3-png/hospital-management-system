(function () {
    "use strict";

    var sidebar = document.querySelector(".sidebar");
    var toggle = document.querySelector("[data-sidebar-toggle]");
    var backdrop;

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove("is-open");
        if (backdrop) {
            backdrop.remove();
            backdrop = null;
        }
    }

    if (toggle && sidebar) {
        toggle.addEventListener("click", function () {
            var open = sidebar.classList.toggle("is-open");
            if (open) {
                backdrop = document.createElement("div");
                backdrop.className = "sidebar-backdrop";
                backdrop.addEventListener("click", closeSidebar);
                document.body.appendChild(backdrop);
            } else {
                closeSidebar();
            }
        });
    }

    document.querySelectorAll("[data-show-toast]").forEach(function (button) {
        button.addEventListener("click", function () {
            var toastElement = document.getElementById(
                button.dataset.showToast,
            );
            if (toastElement && window.bootstrap)
                bootstrap.Toast.getOrCreateInstance(toastElement).show();
        });
    });

    var dateTarget = document.querySelector("[data-current-date]");
    var timeTarget = document.querySelector("[data-current-time]");
    function updateClock() {
        var now = new Date();
        if (dateTarget)
            dateTarget.textContent = now.toLocaleDateString("en-IN", {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric",
            });
        if (timeTarget)
            timeTarget.textContent = now.toLocaleTimeString("en-IN", {
                hour: "2-digit",
                minute: "2-digit",
                hour12: true,
            });
    }
    if (dateTarget || timeTarget) {
        updateClock();
        window.setInterval(updateClock, 30000);
    }

    var dobInput = document.querySelector("[data-date-of-birth]");
    var ageInput = document.querySelector("[data-patient-age]");
    function updateAge() {
        if (!dobInput || !ageInput || !dobInput.value) {
            if (ageInput) ageInput.value = "";
            return;
        }
        var birthDate = new Date(dobInput.value + "T00:00:00");
        var today = new Date();
        
        if (birthDate > today) {
            ageInput.value = "";
            return;
        }

        var years = today.getFullYear() - birthDate.getFullYear();
        var months = today.getMonth() - birthDate.getMonth();
        var days = today.getDate() - birthDate.getDate();

        if (days < 0) {
            months -= 1;
            var prevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
            days += prevMonth.getDate();
        }

        if (months < 0) {
            years -= 1;
            months += 12;
        }

        var ageString = "";
        if (years >= 1) {
            var yStr = years === 1 ? "1 Year" : years + " Years";
            var mStr = months === 1 ? "1 Month" : months + " Months";
            ageString = yStr + " " + mStr;
        } else if (months >= 1) {
            var mStr = months === 1 ? "1 Month" : months + " Months";
            ageString = mStr;
        } else {
            var dStr = days === 1 ? "1 Day" : days + " Days";
            ageString = dStr;
        }
        ageInput.value = ageString;
    }
    if (dobInput && ageInput) {
        dobInput.addEventListener("change", updateAge);
        updateAge();
    }


    document.querySelectorAll("[data-static-form]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            if (!form.checkValidity()) {
                form.reportValidity();
            }
        });
        form.addEventListener("reset", function () {
            window.setTimeout(updateAge, 0);
        });
    });

    var patientList = document.querySelector("[data-patient-list]");
    if (patientList) {
        var patientRows = Array.prototype.slice.call(
            patientList.querySelectorAll("[data-patient-row]"),
        );
        var patientSearch = document.querySelector("[data-patient-search]");
        var filterTabs = document.querySelectorAll("[data-patient-filter]");
        var emptyState = document.querySelector("[data-patient-empty]");
        var loadingState = document.querySelector("[data-patient-loading]");
        var tableWrap = document.querySelector("[data-patient-table]");
        var currentFilter = "all";
        function filterPatients() {
            var query = patientSearch
                ? patientSearch.value.toLowerCase().trim()
                : "";
            var visible = 0;
            patientRows.forEach(function (row) {
                var matchesFilter =
                    currentFilter === "all" ||
                    row.dataset.patientType
                        .split(" ")
                        .indexOf(currentFilter) !== -1;
                var matchesSearch =
                    !query ||
                    row.textContent.toLowerCase().indexOf(query) !== -1;
                var show = matchesFilter && matchesSearch;
                row.hidden = !show;
                if (show) visible += 1;
            });
            if (emptyState) emptyState.hidden = visible !== 0;
            if (tableWrap) tableWrap.hidden = visible === 0;
        }
        if (patientSearch)
            patientSearch.addEventListener("input", filterPatients);
        filterTabs.forEach(function (tab) {
            tab.addEventListener("click", function () {
                currentFilter = tab.dataset.patientFilter;
                filterTabs.forEach(function (item) {
                    item.classList.toggle("active", item === tab);
                });
                if (loadingState && tableWrap) {
                    loadingState.hidden = false;
                    tableWrap.hidden = true;
                    window.setTimeout(function () {
                        loadingState.hidden = true;
                        filterPatients();
                    }, 180);
                } else {
                    filterPatients();
                }
            });
        });
        var clearButton = document.querySelector("[data-patient-clear]");
        if (clearButton)
            clearButton.addEventListener("click", function () {
                if (patientSearch) patientSearch.value = "";
                var allTab = document.querySelector(
                    '[data-patient-filter="all"]',
                );
                if (allTab) allTab.click();
                else filterPatients();
            });
        filterPatients();
    }

    var prescriptionBody = document.querySelector("[data-prescription-body]");
    var addMedicine = document.querySelector("[data-add-medicine]");
    function medicineRow() {
        return '<tr><td><input class="form-control medicine-name" aria-label="Medicine name" placeholder="Medicine name"></td><td><input class="form-control" aria-label="Strength" placeholder="e.g. 250 mg"></td><td><input class="form-control" aria-label="Dosage" placeholder="e.g. 5 ml"></td><td><select class="form-select" aria-label="Frequency"><option>Select</option><option>Once daily</option><option>Twice daily</option><option>Three times daily</option><option>Every 6 hours</option></select></td><td><input class="form-control" aria-label="Duration" placeholder="e.g. 5 days"></td><td><select class="form-select instruction-select" aria-label="Instructions"><option>After Food</option><option>Before Food</option><option>SOS</option><option>At Bedtime</option></select></td><td class="text-end"><button class="btn btn-light btn-sm text-danger" type="button" data-remove-medicine aria-label="Remove medicine"><i class="bi bi-trash"></i></button></td></tr>';
    }
    if (prescriptionBody && addMedicine) {
        addMedicine.addEventListener("click", function () {
            prescriptionBody.insertAdjacentHTML("beforeend", medicineRow());
        });
        prescriptionBody.addEventListener("click", function (event) {
            var removeButton = event.target.closest("[data-remove-medicine]");
            if (!removeButton) return;
            var row = removeButton.closest("tr");
            if (prescriptionBody.rows.length > 1) row.remove();
            else
                row.querySelectorAll("input").forEach(function (input) {
                    input.value = "";
                });
        });
    }

    var labBody = document.querySelector("[data-lab-body]");
    var addTest = document.querySelector("[data-add-test]");
    function labTestRow() {
        return '<tr><td><input class="form-control medicine-name" aria-label="Test name" placeholder="Test name"></td><td><select class="form-select" aria-label="Test category"><option>Hematology</option><option>Biochemistry</option><option>Microbiology</option><option>Radiology</option></select></td><td><select class="form-select" aria-label="Priority"><option>Normal</option><option>Urgent</option></select></td><td><select class="form-select" aria-label="Status"><option>Pending</option><option>Sample Collected</option><option>Processing</option><option>Completed</option></select></td><td><input class="form-control" aria-label="Remarks" placeholder="Optional remarks"></td><td class="text-end"><button class="btn btn-light btn-sm text-danger" type="button" data-remove-test aria-label="Remove test"><i class="bi bi-trash"></i></button></td></tr>';
    }
    if (labBody && addTest) {
        addTest.addEventListener("click", function () {
            labBody.insertAdjacentHTML("beforeend", labTestRow());
        });
        labBody.addEventListener("click", function (event) {
            var removeButton = event.target.closest("[data-remove-test]");
            if (!removeButton) return;
            var row = removeButton.closest("tr");
            if (labBody.rows.length > 1) row.remove();
            else
                row.querySelectorAll("input").forEach(function (input) {
                    input.value = "";
                });
        });
    }

    var billingBody = document.querySelector("[data-billing-body]");
    var addService = document.querySelector("[data-add-service]");
    var paidAmount = document.querySelector("[data-paid-amount]");
    function billingRow() {
        return '<tr><td><select class="form-select medicine-name" aria-label="Service"><option>OPD Consultation</option><option>Follow-up OPD</option><option>Vaccination</option><option>Nebulization</option><option>Laboratory Test</option><option>Medicine</option><option>Other Charges</option></select></td><td><input class="form-control" data-quantity type="number" min="1" value="1" aria-label="Quantity"></td><td><input class="form-control" data-unit-price type="number" min="0" value="0" aria-label="Unit price"></td><td><input class="form-control" data-discount type="number" min="0" value="0" aria-label="Discount"></td><td class="fw-semibold u-nowrap" data-line-total>₹0.00</td><td class="text-end"><button class="btn btn-light btn-sm text-danger" type="button" data-remove-service aria-label="Remove service"><i class="bi bi-trash"></i></button></td></tr>';
    }
    function formatCurrency(value) {
        return (
            "₹" +
            value.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            })
        );
    }
    function calculateBill() {
        if (!billingBody) return;
        var subtotal = 0;
        var discount = 0;
        Array.prototype.forEach.call(billingBody.rows, function (row) {
            var quantity =
                Number(row.querySelector("[data-quantity]").value) || 0;
            var unitPrice =
                Number(row.querySelector("[data-unit-price]").value) || 0;
            var rowDiscount =
                Number(row.querySelector("[data-discount]").value) || 0;
            var lineTotal = Math.max(quantity * unitPrice - rowDiscount, 0);
            subtotal += quantity * unitPrice;
            discount += rowDiscount;
            row.querySelector("[data-line-total]").textContent =
                formatCurrency(lineTotal);
        });
        var grandTotal = Math.max(subtotal - discount, 0);
        var paid = paidAmount ? Number(paidAmount.value) || 0 : 0;
        var values = {
            subtotal: subtotal,
            discount: discount,
            grandTotal: grandTotal,
            balance: Math.max(grandTotal - paid, 0),
        };
        Object.keys(values).forEach(function (key) {
            var target = document.querySelector("[data-billing-" + key + "]");
            if (target) target.textContent = formatCurrency(values[key]);
        });
    }
    if (billingBody && addService) {
        addService.addEventListener("click", function () {
            billingBody.insertAdjacentHTML("beforeend", billingRow());
            calculateBill();
        });
        billingBody.addEventListener("input", calculateBill);
        billingBody.addEventListener("click", function (event) {
            var button = event.target.closest("[data-remove-service]");
            if (button) {
                if (billingBody.rows.length > 1) button.closest("tr").remove();
                calculateBill();
            }
        });
        if (paidAmount) paidAmount.addEventListener("input", calculateBill);
        calculateBill();
    }

    document.querySelectorAll("[data-print-page]").forEach(function (button) {
        button.addEventListener("click", function () {
            window.print();
        });
    });
})();
