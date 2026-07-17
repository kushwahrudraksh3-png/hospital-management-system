/**
 * lab.js — Lab Examination Module
 * Vatsalya Shree Hospital · HMS
 *
 * Single JS file for all lab module pages.
 * Mirrors the patterns used in the parent project's assets/js/app.js
 *
 * Django Integration Notes:
 *   - All data marked as "DEMO DATA" must be replaced by Django template
 *     variables or fetch() API calls once the backend is ready.
 *   - Static forms use data-static-form to prevent default submission.
 *   - Billing totals are calculated client-side and must be confirmed
 *     server-side on save.
 */

(function () {
  'use strict';

  /* ----------------------------------------------------------
     1. SIDEBAR TOGGLE (mobile)
        Same pattern as parent app.js
  ---------------------------------------------------------- */

  var sidebar = document.querySelector('.sidebar');
  var toggle = document.querySelector('[data-sidebar-toggle]');
  var backdrop;

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('is-open');
    if (backdrop) { backdrop.remove(); backdrop = null; }
  }

  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      var open = sidebar.classList.toggle('is-open');
      if (open) {
        backdrop = document.createElement('div');
        backdrop.className = 'sidebar-backdrop';
        backdrop.addEventListener('click', closeSidebar);
        document.body.appendChild(backdrop);
      } else {
        closeSidebar();
      }
    });
  }

  /* ----------------------------------------------------------
     2. LIVE CLOCK
  ---------------------------------------------------------- */

  var dateTarget = document.querySelector('[data-current-date]');
  var timeTarget = document.querySelector('[data-current-time]');

  function updateClock() {
    var now = new Date();
    if (dateTarget) {
      dateTarget.textContent = now.toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
      });
    }
    if (timeTarget) {
      timeTarget.textContent = now.toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit', hour12: true
      });
    }
  }

  if (dateTarget || timeTarget) {
    updateClock();
    window.setInterval(updateClock, 30000);
  }

  /* ----------------------------------------------------------
     3. STATIC FORM GUARD (prevent default submit)
  ---------------------------------------------------------- */

  document.querySelectorAll('[data-static-form]').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); }
    });
  });

  /* ----------------------------------------------------------
     4. TOAST HELPER
  ---------------------------------------------------------- */

  document.querySelectorAll('[data-show-toast]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var el = document.getElementById(btn.dataset.showToast);
      if (el && window.bootstrap) {
        bootstrap.Toast.getOrCreateInstance(el).show();
      }
    });
  });

  /* ----------------------------------------------------------
     5. PRINT PAGE
  ---------------------------------------------------------- */

  document.querySelectorAll('[data-print-page]').forEach(function (btn) {
    btn.addEventListener('click', function () { window.print(); });
  });

  /* ----------------------------------------------------------
     6. TODAY'S PATIENTS TABLE — search + filter
        (mirrors the patient-list pattern from parent app.js)
  ---------------------------------------------------------- */

  var patientList = document.querySelector('[data-lab-patient-list]');
  if (patientList) {
    var patientRows = Array.prototype.slice.call(
      patientList.querySelectorAll('[data-lab-patient-row]')
    );
    var patientSearch = document.querySelector('[data-lab-search]');
    var filterTabs = document.querySelectorAll('[data-lab-filter]');
    var emptyState = document.querySelector('[data-lab-empty]');
    var tableWrap = document.querySelector('[data-lab-table]');
    var currentFilter = 'all';

    function filterLabPatients() {
      var query = patientSearch ? patientSearch.value.toLowerCase().trim() : '';
      var visible = 0;
      patientRows.forEach(function (row) {
        var matchFilter = currentFilter === 'all' ||
          (row.dataset.labStatus && row.dataset.labStatus.split(' ').indexOf(currentFilter) !== -1);
        var matchSearch = !query || row.textContent.toLowerCase().indexOf(query) !== -1;
        var show = matchFilter && matchSearch;
        row.hidden = !show;
        if (show) visible += 1;
      });
      if (emptyState) emptyState.hidden = visible !== 0;
      if (tableWrap) tableWrap.hidden = visible === 0;
    }

    if (patientSearch) {
      patientSearch.addEventListener('input', filterLabPatients);
    }

    filterTabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        currentFilter = tab.dataset.labFilter;
        filterTabs.forEach(function (t) {
          t.classList.toggle('active', t === tab);
        });
        filterLabPatients();
      });
    });

    filterLabPatients();
  }

  /* ----------------------------------------------------------
     7. LAB BILLING — auto-calculate totals from investigation list
        Django integration: replace DEMO_INVESTIGATION_PRICES with
        server-rendered JSON: {{ investigation_prices|json }}
  ---------------------------------------------------------- */

  // DEMO DATA — replace with Django context variable
  var INVESTIGATION_PRICES = {
    'Complete Blood Count (CBC)': 250,
    'ESR': 80,
    'Peripheral Blood Smear': 150,
    'Platelet Count': 100,
    'Blood Group & Rh': 80,
    'Haemoglobin (Hb)': 60,
    'Blood Glucose (Fasting)': 70,
    'Blood Glucose (PP)': 70,
    'Random Blood Sugar (RBS)': 60,
    'HbA1c': 350,
    'Lipid Profile': 450,
    'Liver Function Test (LFT)': 550,
    'Kidney Function Test (KFT)': 500,
    'Serum Creatinine': 150,
    'Uric Acid': 120,
    'Calcium': 150,
    'Sodium / Potassium': 200,
    'Thyroid Profile (T3, T4, TSH)': 650,
    'TSH': 280,
    'C-Reactive Protein (CRP)': 300,
    'Widal Test': 200,
    'Dengue NS1 Antigen': 500,
    'Dengue IgG / IgM': 500,
    'Malaria Antigen (Card Test)': 250,
    'Typhoid IgG / IgM (Typhi Dot)': 350,
    'Blood Culture & Sensitivity': 700,
    'Urine Routine Microscopy': 100,
    'Urine Culture & Sensitivity': 500,
    'Stool Routine Examination': 120,
    'HBsAg (Hepatitis B)': 200,
    'Anti-HCV (Hepatitis C)': 300,
    'HIV I & II (ELISA)': 300,
    'VDRL (Syphilis)': 150,
    'RA Factor': 200,
    'ASO Titre': 220,
    'ANA Screen': 800,
    'X-Ray Chest (PA View)': 350,
    'X-Ray Any Part': 300,
    'Ultrasonography Abdomen': 800,
    'Ultrasonography Pelvis': 600,
    'ECG': 200,
    'Semen Analysis': 500,
    'Pap Smear': 400
  };

  /* Lab billing table rows */
  var labBillingBody = document.querySelector('[data-lab-billing-body]');

  function formatINR(value) {
    return '₹' + value.toLocaleString('en-IN', {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    });
  }

  function calculateLabBill() {
    if (!labBillingBody) return;
    var subtotal = 0;
    Array.prototype.forEach.call(labBillingBody.rows, function (row) {
      var priceCell = row.querySelector('[data-test-price]');
      var price = priceCell ? Number(priceCell.dataset.testPrice) || 0 : 0;
      subtotal += price;
      if (priceCell) priceCell.textContent = formatINR(price);
    });
    var totalEl = document.querySelector('[data-lab-bill-total]');
    var grandTotalEl = document.querySelector('[data-lab-bill-grand-total]');
    var wordsEl = document.querySelector('[data-lab-bill-words]');
    if (totalEl) totalEl.textContent = formatINR(subtotal);
    if (grandTotalEl) grandTotalEl.textContent = formatINR(subtotal);
    if (wordsEl) wordsEl.textContent = amountInWords(subtotal);
  }

  /* Lookup price for a test name */
  function getPriceForTest(testName) {
    return INVESTIGATION_PRICES[testName] || 0;
  }

  /* Convert rupee amount to words (simplified) */
  function amountInWords(amount) {
    var ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven',
      'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen',
      'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    var tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty',
      'Seventy', 'Eighty', 'Ninety'];

    function convert(n) {
      if (n < 20) return ones[n];
      if (n < 100) return tens[Math.floor(n / 10)] + (n % 10 ? ' ' + ones[n % 10] : '');
      if (n < 1000) return ones[Math.floor(n / 100)] + ' Hundred' + (n % 100 ? ' ' + convert(n % 100) : '');
      if (n < 100000) return convert(Math.floor(n / 1000)) + ' Thousand' + (n % 1000 ? ' ' + convert(n % 1000) : '');
      return convert(Math.floor(n / 100000)) + ' Lakh' + (n % 100000 ? ' ' + convert(n % 100000) : '');
    }

    if (amount === 0) return 'Zero Rupees Only';
    var result = convert(Math.floor(amount));
    return result + ' Rupees Only';
  }

  if (labBillingBody) {
    calculateLabBill();
    labBillingBody.addEventListener('change', calculateLabBill);
  }

  /* ----------------------------------------------------------
     8. REPORT ENTRY — result input + flag indicator
  ---------------------------------------------------------- */

  var reportEntryBody = document.querySelector('[data-report-entry-body]');
  if (reportEntryBody) {
    reportEntryBody.addEventListener('input', function (event) {
      var input = event.target;
      if (!input.hasAttribute('data-result-input')) return;
      var row = input.closest('tr');
      if (!row) return;
      var min = parseFloat(row.dataset.refMin);
      var max = parseFloat(row.dataset.refMax);
      var val = parseFloat(input.value);
      var flagCell = row.querySelector('[data-flag-cell]');
      if (!flagCell || isNaN(val)) return;
      if (!isNaN(min) && !isNaN(max)) {
        if (val < min) {
          flagCell.textContent = '▼ Low';
          flagCell.className = 'result-flag-low';
        } else if (val > max) {
          flagCell.textContent = '▲ High';
          flagCell.className = 'result-flag-high';
        } else {
          flagCell.textContent = '● Normal';
          flagCell.className = 'result-flag-normal';
        }
      }
    });
  }

  /* ----------------------------------------------------------
     9. SEND TO DOCTOR — status update (frontend only)
        Django integration: replace with fetch() POST to
        /lab/api/send-report/<id>/
  ---------------------------------------------------------- */

  var sendDoctorBtn = document.querySelector('[data-send-to-doctor]');
  if (sendDoctorBtn) {
    sendDoctorBtn.addEventListener('click', function () {
      var statusBadge = document.querySelector('[data-report-status-badge]');
      if (statusBadge) {
        statusBadge.textContent = 'Report Sent';
        statusBadge.className = 'badge badge-soft-success';
      }
      sendDoctorBtn.disabled = true;
      sendDoctorBtn.innerHTML = '<i class="bi bi-check2-circle"></i> Report Sent';
      var toast = document.getElementById('toastReportSent');
      if (toast && window.bootstrap) {
        bootstrap.Toast.getOrCreateInstance(toast).show();
      }
    });
  }

  /* ----------------------------------------------------------
     10. COMPLETE REPORT — status update (frontend only)
         Django integration: replace with fetch() POST to
         /lab/api/complete-report/<id>/
  ---------------------------------------------------------- */

  var completeReportBtn = document.querySelector('[data-complete-report]');
  if (completeReportBtn) {
    completeReportBtn.addEventListener('click', function () {
      var statusBadge = document.querySelector('[data-report-status-badge]');
      if (statusBadge) {
        statusBadge.textContent = 'Report Ready';
        statusBadge.className = 'badge badge-soft-ready';
      }
      var toast = document.getElementById('toastReportReady');
      if (toast && window.bootstrap) {
        bootstrap.Toast.getOrCreateInstance(toast).show();
      }
    });
  }

  /* ----------------------------------------------------------
     11. LOAD DOCTOR PRESCRIPTION FROM LOCALSTORAGE
  ---------------------------------------------------------- */
  document.addEventListener('DOMContentLoaded', function () {
    var savedDataStr = localStorage.getItem('saved_prescription_PT-2026-081');
    if (savedDataStr) {
      try {
        var savedData = JSON.parse(savedDataStr);

        // Fill demographics dynamically if elements exist
        var fieldValues = document.querySelectorAll('.field-value-dotted');
        if (fieldValues.length >= 6) {
          if (savedData.patientName) fieldValues[0].textContent = savedData.patientName;
          if (savedData.patientAge && savedData.patientGender) {
            var genderShort = savedData.patientGender.charAt(0).toUpperCase();
            fieldValues[1].textContent = savedData.patientAge + ' / ' + genderShort;
          }
          if (savedData.vitals && savedData.vitals.weight) fieldValues[2].textContent = savedData.vitals.weight + ' kg';
          if (savedData.vitals && savedData.vitals.height) fieldValues[3].textContent = savedData.vitals.height + ' cm';
          if (savedData.chiefComplaint) fieldValues[4].textContent = savedData.chiefComplaint;
          if (savedData.patientAddress) fieldValues[5].textContent = savedData.patientAddress;
        }

        // Fill vitals sidebar if elements exist
        var vitalLines = document.querySelectorAll('.vital-line-value-underlined');
        if (vitalLines.length >= 5 && savedData.vitals) {
          if (savedData.vitals.heartRate) vitalLines[0].textContent = savedData.vitals.heartRate + ' bpm';
          if (savedData.vitals.spo2) vitalLines[2].textContent = savedData.vitals.spo2 + '%';
          if (savedData.vitals.temperature) vitalLines[3].textContent = savedData.vitals.temperature + ' °F';
          if (savedData.vitals.bp) vitalLines[4].textContent = savedData.vitals.bp;
        }

        // Fill left panel examinations list if elements exist
        var leftPanelEntries = document.querySelectorAll('.body-left-panel .prescription-text-entry');
        if (leftPanelEntries.length >= 6) {
          if (savedData.examinations) leftPanelEntries[0].textContent = savedData.examinations;
          if (savedData.investigations) leftPanelEntries[5].textContent = savedData.investigations;
        }

        // Render canvas drawing image
        var rxImg = document.getElementById('handwrittenRxImg');
        var rxContent = document.getElementById('staticRxContent');
        if (rxImg && savedData.canvasDrawing) {
          rxImg.src = savedData.canvasDrawing;
          rxImg.style.display = 'block';
          if (rxContent) {
            rxContent.style.display = 'none';
          }
        }
      } catch (e) {
        console.error('Error loading doctor prescription data:', e);
      }
    }
  });

}());
