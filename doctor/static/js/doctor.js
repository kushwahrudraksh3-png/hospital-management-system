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
            const patientType = row.dataset.patientType || 'all';

            const matchesQuery = patientName.includes(query) || patientId.includes(query);
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

    // Undo/Redo Stacks
    let undoStack = [];
    let redoStack = [];

    const saveState = () => {
        if (undoStack.length >= 20) {
            undoStack.shift();
        }
        undoStack.push(canvas.toDataURL());
        redoStack = []; // Clear redo stack on new action
    };

    // Resize canvas
    const resizeCanvas = () => {
        const rect = canvas.parentElement.getBoundingClientRect();
        // Set canvas backing store width and height keeping A4 aspect ratio (1 / 1.414)
        canvas.width = rect.width;
        canvas.height = rect.width * 1.414;

        // Reset context properties after resize
        ctx.strokeStyle = isEraser ? '#ffffff' : '#1e3a8a';
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.lineWidth = isEraser ? 15 : 2.5;

        // If there's an image on the stack, restore it
        if (undoStack.length > 0) {
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = undoStack[undoStack.length - 1];
        } else {
            // Draw a white background on initial load
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
    };

    // Initial resize
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Save initial blank state
    saveState();

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
    };

    const draw = (e) => {
        if (!isDrawing) return;
        e.preventDefault(); // Prevent scrolling on touch devices
        const coords = getCoordinates(e);

        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();

        lastX = coords.x;
        lastY = coords.y;
    };

    const stopDrawing = () => {
        if (isDrawing) {
            isDrawing = false;
            saveState();
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
            ctx.lineWidth = 2.5;
            penBtn.classList.add('active');
            eraserBtn.classList.remove('active');
        });

        eraserBtn.addEventListener('click', () => {
            isEraser = true;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 15;
            eraserBtn.classList.add('active');
            penBtn.classList.remove('active');
        });
    }

    if (undoBtn) {
        undoBtn.addEventListener('click', () => {
            if (undoStack.length > 1) {
                const currentState = undoStack.pop();
                redoStack.push(currentState);
                const prevState = undoStack[undoStack.length - 1];

                const img = new Image();
                img.onload = () => {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                };
                img.src = prevState;
            }
        });
    }

    if (redoBtn) {
        redoBtn.addEventListener('click', () => {
            if (redoStack.length > 0) {
                const nextState = redoStack.pop();
                undoStack.push(nextState);

                const img = new Image();
                img.onload = () => {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                };
                img.src = nextState;
            }
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            saveState();
        });
    }

    // Save Action Button
    const saveActionBtn = document.getElementById('saveHandwrittenPrescriptionBtn');
    if (saveActionBtn) {
        saveActionBtn.addEventListener('click', () => {
            const dataUrl = canvas.toDataURL('image/png');
            alert('Handwritten Prescription Saved!');
            console.log(dataUrl);
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

// ============================================
// Patient Summary
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleEmptyStateBtn');
    const tableContainer = document.getElementById('consultationTableContainer');
    const emptyState = document.getElementById('consultationEmptyState');
    if (toggleBtn && tableContainer && emptyState) {
        toggleBtn.addEventListener('click', () => {
            if (tableContainer.classList.contains('d-none')) {
                tableContainer.classList.remove('d-none');
                emptyState.classList.add('d-none');
                toggleBtn.innerHTML = '<i class="bi bi-shuffle"></i> Toggle Empty State';
            } else {
                tableContainer.classList.add('d-none');
                emptyState.classList.remove('d-none');
                toggleBtn.innerHTML = '<i class="bi bi-shuffle"></i> Toggle Table';
            }
        });
    }
});

