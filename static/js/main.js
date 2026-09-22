/**
 * AnnSeva - Main Frontend JavaScript (main.js)
 * Handles mobile navbar toggle, alert dismissals, demo credential quick-fill,
 * and live background polling for alerts and counters.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Menu Toggle
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function () {
            navMenu.classList.toggle('show');
        });
    }

    // 2. Alert Dismiss Buttons
    const alertCloses = document.querySelectorAll('.alert-close');
    alertCloses.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const alertBox = btn.closest('.alert');
            if (alertBox) {
                alertBox.style.opacity = '0';
                setTimeout(() => alertBox.remove(), 250);
            }
        });
    });

    // 3. Quick-Fill Demo Credentials Helper (Viva Convenience)
    window.fillCredentials = function (email, password) {
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        if (emailInput && passwordInput) {
            emailInput.value = email;
            passwordInput.value = password;
            // Visual highlight
            emailInput.style.backgroundColor = '#ecfdf5';
            passwordInput.style.backgroundColor = '#ecfdf5';
            setTimeout(() => {
                emailInput.style.backgroundColor = '';
                passwordInput.style.backgroundColor = '';
            }, 600);
        }
    };

    // 4. Live Background Polling (Updates notification counters in real time)
    function pollLiveStatus() {
        fetch('/api/live-status')
            .then(res => res.json())
            .then(data => {
                // Find Alerts nav link
                const alertsLink = document.querySelector('a[href*="/notifications"]');
                if (alertsLink) {
                    let badge = alertsLink.querySelector('.badge-counter');
                    if (data.unread_notifications > 0) {
                        if (!badge) {
                            badge = document.createElement('span');
                            badge.className = 'badge-counter';
                            alertsLink.appendChild(badge);
                        }
                        badge.textContent = data.unread_notifications;
                        badge.style.display = 'inline-block';
                    } else if (badge) {
                        badge.style.display = 'none';
                    }
                }
            })
            .catch(() => {}); // silent fail if network offline
    }

    // Run live polling every 5 seconds
    setInterval(pollLiveStatus, 5000);

    // 5. Phone Number Input Real-Time Validation & Character Prevention
    // Strictly enforces digits only (0-9), preventing letters, variables, and symbols
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name="phone"]');
    phoneInputs.forEach(function (input) {
        input.setAttribute('inputmode', 'numeric');
        input.setAttribute('maxlength', '10');
        input.setAttribute('pattern', '[0-9]{10}');

        // Block non-digit keypress events directly
        input.addEventListener('keypress', function (e) {
            if (e.isComposing || e.ctrlKey || e.altKey || e.metaKey) return;
            if (e.charCode < 48 || e.charCode > 57) {
                e.preventDefault();
                return false;
            }
        });

        // Real-time stripping of any non-digit characters on input
        input.addEventListener('input', function () {
            const clean = this.value.replace(/[^0-9]/g, '').slice(0, 10);
            if (this.value !== clean) {
                this.value = clean;
            }
        });

        // Clean clipboard on paste to ensure numbers only
        input.addEventListener('paste', function (e) {
            e.preventDefault();
            const clipboardData = e.clipboardData || window.clipboardData;
            if (!clipboardData) return;
            const text = clipboardData.getData('text');
            const clean = text.replace(/[^0-9]/g, '').slice(0, 10);
            const start = this.selectionStart || 0;
            const end = this.selectionEnd || 0;
            const val = this.value;
            const newVal = (val.substring(0, start) + clean + val.substring(end)).replace(/[^0-9]/g, '').slice(0, 10);
            this.value = newVal;
        });
    });
});
