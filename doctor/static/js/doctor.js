// ============================================
// Sidebar
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Mobile Toggle
    const toggleBtn = document.querySelector('[data-sidebar-toggle]');
    const sidebar = document.querySelector('.sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('is-open');
        });
    }
});

// ============================================
// Navbar
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    const dateTarget = document.querySelector('[data-current-date]');
    if (dateTarget) {
        const now = new Date();
        dateTarget.textContent = now.toLocaleDateString("en-IN", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
        });
    }
});

// ============================================
// Dashboard
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Current time widget update
    const updateTimeWidget = () => {
        const timeWidget = document.querySelector('[data-current-time]');
        if (timeWidget) {
            const now = new Date();
            timeWidget.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    };
    updateTimeWidget();
    setInterval(updateTimeWidget, 60000);
});

// ============================================
// Patient Search
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchName');
    const typeSelect = document.getElementById('patientType');
    const searchBtn = document.querySelector('[data-search-btn]');
    const tableRows = document.querySelectorAll('.table tbody tr');

    function filterPatients() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectedType = typeSelect ? typeSelect.value : 'all';

        tableRows.forEach(row => {
            const patientId = row.cells[0] ? row.cells[0].textContent.toLowerCase().trim() : '';
            const patientName = row.cells[1] ? row.cells[1].textContent.toLowerCase().trim() : '';
            const fatherName = row.cells[2] ? row.cells[2].textContent.toLowerCase().trim() : '';
            const contact = row.cells[3] ? row.cells[3].textContent.toLowerCase().trim() : '';
            const patientType = row.dataset.patientType || 'all';

            const matchesQuery = patientName.includes(query) || 
                                 patientId.includes(query) || 
                                 fatherName.includes(query) || 
                                 contact.includes(query);
            const matchesType = (selectedType === 'all') || (patientType === selectedType);

            if (matchesQuery && matchesType) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', filterPatients);
    }
    if (typeSelect) {
        typeSelect.addEventListener('change', filterPatients);
    }
    if (searchBtn) {
        searchBtn.addEventListener('click', filterPatients);
    }
});

// ============================================
// Queue
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Queue Search Filter
    const searchInput = document.querySelector('[data-queue-search]');
    const tableRows = document.querySelectorAll('.queue-table tbody tr');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            tableRows.forEach(row => {
                const patientName = row.querySelector('.patient-name').textContent.toLowerCase();
                const patientId = row.querySelector('.patient-id').textContent.toLowerCase();
                if (patientName.includes(query) || patientId.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Status Filter Tabs
    const filterTabs = document.querySelectorAll('[data-filter-tab]');
    if (filterTabs.length > 0) {
        filterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                filterTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const filter = tab.dataset.filterTab;
                tableRows.forEach(row => {
                    const status = row.dataset.status;
                    if (filter === 'all' || status === filter) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                    
                    // Toggle buttons and badges for lab-request patients based on active tab
                    if (status === 'lab-request') {
                        const viewRxBtn = row.querySelector('.btn-view-rx-lab');
                        const examineBtn = row.querySelector('.btn-examine-lab');
                        const normalLabBadge = row.querySelector('.badge-normal-lab');
                        const requestedLabBadge = row.querySelector('.badge-requested-lab');
                        
                        if (viewRxBtn && examineBtn) {
                            if (filter === 'lab-request') {
                                viewRxBtn.style.display = 'inline-block';
                                examineBtn.style.display = 'none';
                            } else {
                                viewRxBtn.style.display = 'none';
                                examineBtn.style.display = 'inline-block';
                            }
                        }
                        
                        if (normalLabBadge && requestedLabBadge) {
                            if (filter === 'lab-request') {
                                normalLabBadge.style.display = 'none';
                                requestedLabBadge.style.display = 'inline-block';
                            } else {
                                normalLabBadge.style.display = 'inline-block';
                                requestedLabBadge.style.display = 'none';
                            }
                        }
                    }
                });
            });
        });
    }
});

// ============================================
// Examination
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Basic calculator for BMI if height and weight are entered
    const weightInput = document.querySelector('[data-vital="weight"]');
    const heightInput = document.querySelector('[data-vital="height"]');
    const bmiDisplay = document.querySelector('[data-vital-display="bmi"]');

    const calculateBMI = () => {
        if (weightInput && heightInput && bmiDisplay) {
            const weight = parseFloat(weightInput.value);
            const heightCm = parseFloat(heightInput.value);
            if (weight > 0 && heightCm > 0) {
                const heightM = heightCm / 100;
                const bmi = weight / (heightM * heightM);
                bmiDisplay.textContent = bmi.toFixed(1);
            }
        }
    };

    if (weightInput && heightInput) {
        weightInput.addEventListener('input', calculateBMI);
        heightInput.addEventListener('input', calculateBMI);
    }

    // Handle saving clinical examination
    const examForm = document.querySelector('[data-exam-form]');
    if (examForm) {
        examForm.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Clinical Examination Saved Successfully!');
            window.location.href = 'prescription.html';
        });
    }
});

// ============================================
// Prescription
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    const addRowBtn = document.querySelector('[data-add-medicine]');
    const tableBody = document.querySelector('[data-prescription-body]');

    if (addRowBtn && tableBody) {
        addRowBtn.addEventListener('click', () => {
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td><input class="form-control medicine-name" aria-label="Medicine name" placeholder="Enter medicine name"></td>
                <td><input class="form-control" aria-label="Strength" placeholder="Strength (e.g. 500mg)"></td>
                <td><input class="form-control" aria-label="Dosage" placeholder="Dosage (e.g. 1 tab)"></td>
                <td>
                    <select class="form-select" aria-label="Frequency">
                        <option>Once daily</option>
                        <option>Twice daily</option>
                        <option>Three times daily</option>
                        <option>Every 6 hours</option>
                    </select>
                </td>
                <td><input class="form-control" aria-label="Duration" placeholder="Duration (e.g. 5 days)"></td>
                <td>
                    <select class="form-select instruction-select" aria-label="Instructions">
                        <option>After Food</option>
                        <option>Before Food</option>
                        <option>SOS</option>
                        <option>At Bedtime</option>
                    </select>
                </td>
                <td class="text-end">
                    <button class="btn btn-light btn-sm text-danger" type="button" data-remove-medicine aria-label="Remove medicine">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(newRow);
        });

        // Event delegation for removing rows
        tableBody.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('[data-remove-medicine]');
            if (removeBtn) {
                const row = removeBtn.closest('tr');
                if (row) {
                    if (tableBody.querySelectorAll('tr').length > 1) {
                        row.remove();
                    } else {
                        alert("At least one medicine row must remain.");
                    }
                }
            }
        });
    }
});

// ============================================
// Handwriting
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('handwritingCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let isEraser = false;
    let lastX = 0;
    let lastY = 0;

    let strokes = [];
    let redoStrokes = [];
    let currentStroke = null;

    // Load initial strokes if any
    const savedStrokesEl = document.getElementById('saved-strokes-data');
    if (savedStrokesEl) {
        try {
            strokes = JSON.parse(savedStrokesEl.textContent) || [];
        } catch (e) {
            console.error('Failed to parse saved strokes:', e);
        }
    }

    const redrawCanvasFromStrokes = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Scale stroke thickness dynamically relative to canvas width
        const scaleFactor = canvas.width / 800; // base scale width
        
        strokes.forEach(stroke => {
            if (!stroke.points || stroke.points.length === 0) return;
            
            ctx.beginPath();
            ctx.strokeStyle = stroke.isEraser ? 'rgba(0,0,0,1)' : '#1e3a8a';
            ctx.globalCompositeOperation = stroke.isEraser ? 'destination-out' : 'source-over';
            ctx.lineJoin = 'round';
            ctx.lineCap = 'round';
            ctx.lineWidth = (stroke.isEraser ? 15 : 2.5) * scaleFactor;
            
            const firstPt = stroke.points[0];
            ctx.moveTo(firstPt.x * canvas.width, firstPt.y * canvas.height);
            
            for (let i = 1; i < stroke.points.length; i++) {
                const pt = stroke.points[i];
                ctx.lineTo(pt.x * canvas.width, pt.y * canvas.height);
            }
            ctx.stroke();
        });
    };

    // Resize canvas
    const resizeCanvas = () => {
        const parent = canvas.parentElement;
        const rect = parent.getBoundingClientRect();

        // Fixed A4 aspect ratio: 210mm x 297mm = 1 : 1.414
        const targetHeight = rect.width * 1.414;
        parent.style.height = `${targetHeight}px`;

        canvas.width = rect.width;
        canvas.height = targetHeight;

        // Scale background pad to fit wrapper width
        const pad = parent.querySelector('.prescription-pad');
        if (pad) {
            const scale = rect.width / 793.7; // 210mm ≈ 793.7px at 96dpi
            pad.style.transform = `scale(${scale})`;
            pad.style.transformOrigin = 'top left';
        }

        // Reset context properties after resize
        ctx.strokeStyle = isEraser ? 'rgba(0,0,0,1)' : '#1e3a8a';
        ctx.globalCompositeOperation = isEraser ? 'destination-out' : 'source-over';
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.lineWidth = (isEraser ? 15 : 2.5) * (canvas.width / 800);

        // Restore strokes
        redrawCanvasFromStrokes();
    };

    // Initial resize
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Drawing Logic
    const getCoordinates = (e) => {
        const rect = canvas.getBoundingClientRect();
        // Scale client coordinates back to match backing store dimensions
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
            x: ((clientX - rect.left) / rect.width) * canvas.width,
            y: ((clientY - rect.top) / rect.height) * canvas.height
        };
    };

    const startDrawing = (e) => {
        isDrawing = true;
        const coords = getCoordinates(e);
        lastX = coords.x;
        lastY = coords.y;

        // Initialize a new scale-independent stroke
        currentStroke = {
            isEraser: isEraser,
            points: [{
                x: coords.x / canvas.width,
                y: coords.y / canvas.height
            }]
        };
    };

    const draw = (e) => {
        if (!isDrawing || !currentStroke) return;
        e.preventDefault(); // Prevent scrolling on touch devices
        const coords = getCoordinates(e);

        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(coords.x, coords.y);
        
        ctx.strokeStyle = isEraser ? 'rgba(0,0,0,1)' : '#1e3a8a';
        ctx.globalCompositeOperation = isEraser ? 'destination-out' : 'source-over';
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.lineWidth = (isEraser ? 15 : 2.5) * (canvas.width / 800);
        ctx.stroke();

        lastX = coords.x;
        lastY = coords.y;

        // Append normalized points
        currentStroke.points.push({
            x: coords.x / canvas.width,
            y: coords.y / canvas.height
        });
    };

    const stopDrawing = () => {
        if (isDrawing && currentStroke) {
            isDrawing = false;
            strokes.push(currentStroke);
            currentStroke = null;
            redoStrokes = []; // Clear redo stack on new action
        }
    };

    // Mouse Events
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);

    // Touch Events (Stylus/Tablet)
    canvas.addEventListener('touchstart', startDrawing, { passive: false });
    canvas.addEventListener('touchmove', draw, { passive: false });
    canvas.addEventListener('touchend', stopDrawing);

    // Toolbar Buttons
    const penBtn = document.getElementById('canvasPenBtn');
    const eraserBtn = document.getElementById('canvasEraserBtn');
    const undoBtn = document.getElementById('canvasUndoBtn');
    const redoBtn = document.getElementById('canvasRedoBtn');
    const clearBtn = document.getElementById('canvasClearBtn');

    if (penBtn && eraserBtn) {
        penBtn.addEventListener('click', () => {
            isEraser = false;
            ctx.strokeStyle = '#1e3a8a';
            ctx.globalCompositeOperation = 'source-over';
            ctx.lineWidth = 2.5 * (canvas.width / 800);
            penBtn.classList.add('active');
            eraserBtn.classList.remove('active');
        });

        eraserBtn.addEventListener('click', () => {
            isEraser = true;
            ctx.strokeStyle = 'rgba(0,0,0,1)';
            ctx.globalCompositeOperation = 'destination-out';
            ctx.lineWidth = 15 * (canvas.width / 800);
            eraserBtn.classList.add('active');
            penBtn.classList.remove('active');
        });
    }

    if (undoBtn) {
        undoBtn.addEventListener('click', () => {
            if (strokes.length > 0) {
                const popped = strokes.pop();
                redoStrokes.push(popped);
                redrawCanvasFromStrokes();
            }
        });
    }

    if (redoBtn) {
        redoBtn.addEventListener('click', () => {
            if (redoStrokes.length > 0) {
                const popped = redoStrokes.pop();
                strokes.push(popped);
                redrawCanvasFromStrokes();
            }
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            strokes = [];
            redoStrokes = [];
            redrawCanvasFromStrokes();
        });
    }

    // Save Action Button
    const saveActionBtn = document.getElementById('saveHandwrittenPrescriptionBtn');
    if (saveActionBtn) {
        saveActionBtn.addEventListener('click', async () => {
            const visitId = saveActionBtn.dataset.visitId;
            const patientId = saveActionBtn.dataset.patientId;

            if (!visitId || !patientId) {
                alert('Error: Missing visit or patient information.');
                return;
            }

            // Check html2canvas is loaded
            if (typeof html2canvas === 'undefined') {
                alert('Error: Page capture library not loaded. Please refresh and try again.');
                return;
            }

            // Disable button and show loading state
            const originalHTML = saveActionBtn.innerHTML;
            saveActionBtn.disabled = true;
            saveActionBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Capturing...';

            try {
                const wrapper = canvas.parentElement;

                // Capture the entire prescription wrapper (background + handwriting)
                const compositeCanvas = await html2canvas(wrapper, {
                    scale: 2,                // High-resolution output (2x)
                    useCORS: true,           // Allow cross-origin images (logos)
                    allowTaint: true,
                    backgroundColor: '#ffffff',
                    logging: false,
                });

                const dataUrl = compositeCanvas.toDataURL('image/png');
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

                saveActionBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

                const response = await fetch('/doctor/save-prescription/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        visit_id: visitId,
                        patient_id: patientId,
                        image_data: dataUrl,
                        canvas_data: strokes,
                    }),
                });

                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    saveActionBtn.innerHTML = '<i class="bi bi-check-circle"></i> Saved!';
                    saveActionBtn.classList.remove('btn-primary');
                    saveActionBtn.classList.add('btn-success');
                    setTimeout(() => {
                        saveActionBtn.innerHTML = originalHTML;
                        saveActionBtn.classList.remove('btn-success');
                        saveActionBtn.classList.add('btn-primary');
                        saveActionBtn.disabled = false;
                    }, 2000);
                } else {
                    alert('Error: ' + (result.message || 'Failed to save prescription.'));
                    saveActionBtn.innerHTML = originalHTML;
                    saveActionBtn.disabled = false;
                }
            } catch (err) {
                console.error('Prescription save error:', err);
                alert('Error capturing prescription. Please try again.');
                saveActionBtn.innerHTML = originalHTML;
                saveActionBtn.disabled = false;
            }
        });
    }
});

// ============================================
// Reports
// ============================================
/* Lab Reports specific logic */

// ============================================
// Printing
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Standard Print trigger
    const printBtn = document.querySelector('[data-print-trigger]');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // PDF Download trigger
    const downloadPdfBtn = document.querySelector('[data-download-pdf-trigger]');
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // Auto-trigger print for pages marked with auto-print-page class
    if (document.body.classList.contains('auto-print-page')) {
        setTimeout(() => {
            window.print();
        }, 500);
    }
});

// ============================================
// Common Utility Functions
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Global back button listener replacing inline window.history.back()
    const backButtons = document.querySelectorAll('[data-back-btn]');
    backButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            window.history.back();
        });
    });

    // Profile save confirmation alert
    const profileSaveBtn = document.querySelector('[data-profile-save]');
    if (profileSaveBtn) {
        profileSaveBtn.addEventListener('click', () => {
            alert('Profile Updated!');
        });
    }
});


