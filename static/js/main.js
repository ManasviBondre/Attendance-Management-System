/**
 * Attendance Management System - Frontend Interactivity
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Password Visibility Toggle
    const togglePasswordButtons = document.querySelectorAll('.toggle-password-btn');
    togglePasswordButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                const isPassword = targetInput.type === 'password';
                targetInput.type = isPassword ? 'text' : 'password';
                
                // Toggle eye icon if present
                const icon = this.querySelector('i');
                if (icon) {
                    if (isPassword) {
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                    } else {
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                    }
                }
            }
        });
    });

    // 2. Real-time Table Filter / Search
    const searchInputs = document.querySelectorAll('.table-search-input');
    searchInputs.forEach(input => {
        const targetTableId = input.getAttribute('data-table');
        const table = document.getElementById(targetTableId);
        if (table) {
            input.addEventListener('keyup', function () {
                const term = this.value.toLowerCase().trim();
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    if (text.includes(term)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        }
    });

    // 3. Attendance Marker Shortcuts & Live Counter
    const attendanceForm = document.getElementById('attendanceMarkerForm');
    if (attendanceForm) {
        const markAllPresentBtn = document.getElementById('markAllPresentBtn');
        const markAllAbsentBtn = document.getElementById('markAllAbsentBtn');
        const presentCountEl = document.getElementById('livePresentCount');
        const absentCountEl = document.getElementById('liveAbsentCount');
        const totalCountEl = document.getElementById('liveTotalCount');
        const pctEl = document.getElementById('livePercentage');

        function updateLiveCounts() {
            const allRadios = attendanceForm.querySelectorAll('input[type="radio"]:checked');
            let present = 0;
            let absent = 0;

            allRadios.forEach(radio => {
                if (radio.value === 'Present') {
                    present++;
                } else if (radio.value === 'Absent') {
                    absent++;
                }
            });

            const total = present + absent;
            if (presentCountEl) presentCountEl.textContent = present;
            if (absentCountEl) absentCountEl.textContent = absent;
            if (totalCountEl) totalCountEl.textContent = total;
            if (pctEl && total > 0) {
                const pct = ((present / total) * 100).toFixed(1);
                pctEl.textContent = pct + '%';
            }
        }

        if (markAllPresentBtn) {
            markAllPresentBtn.addEventListener('click', function () {
                const presentRadios = attendanceForm.querySelectorAll('input[type="radio"][value="Present"]');
                presentRadios.forEach(r => {
                    r.checked = true;
                });
                updateLiveCounts();
            });
        }

        if (markAllAbsentBtn) {
            markAllAbsentBtn.addEventListener('click', function () {
                const absentRadios = attendanceForm.querySelectorAll('input[type="radio"][value="Absent"]');
                absentRadios.forEach(r => {
                    r.checked = true;
                });
                updateLiveCounts();
            });
        }

        // Listen for individual radio changes
        const radios = attendanceForm.querySelectorAll('input[type="radio"]');
        radios.forEach(r => {
            r.addEventListener('change', updateLiveCounts);
        });

        // Initialize count on page load
        updateLiveCounts();
    }

    // 4. Registration Role Selector Dynamic Fields
    const roleSelect = document.getElementById('registrationRoleSelect');
    if (roleSelect) {
        const studentFields = document.getElementById('studentSpecificFields');
        const facultyFields = document.getElementById('facultySpecificFields');
        const adminFields = document.getElementById('adminSpecificFields');

        function toggleRoleFields() {
            const selected = roleSelect.value;
            if (studentFields) studentFields.style.display = (selected === 'student') ? 'block' : 'none';
            if (facultyFields) facultyFields.style.display = (selected === 'faculty') ? 'block' : 'none';
            if (adminFields) adminFields.style.display = (selected === 'admin') ? 'block' : 'none';
        }

        roleSelect.addEventListener('change', toggleRoleFields);
        toggleRoleFields();
    }

    // 5. Auto dismiss alerts after 5 seconds
    const autoDismissAlerts = document.querySelectorAll('.alert-dismissible');
    autoDismissAlerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                // Ignore if bootstrap is not yet loaded
            }
        }, 6000);
    });
});
