document.addEventListener('DOMContentLoaded', () => {
    // Password / Confirm Password Toggle Functionality
    function setupPasswordToggle(inputId, toggleId, iconId) {
        const input = document.getElementById(inputId);
        const toggle = document.getElementById(toggleId);
        const icon = document.getElementById(iconId);

        if (input && toggle && icon) {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('bi-eye');
                    icon.classList.add('bi-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.remove('bi-eye-slash');
                    icon.classList.add('bi-eye');
                }
            });
        }
    }

    setupPasswordToggle('password', 'togglePassword', 'toggleIcon');
    setupPasswordToggle('confirm_password', 'toggleConfirmPassword', 'toggleConfirmIcon');

    // OTP Input Handling
    const otpForm = document.getElementById('otpForm');
    const otpCodeInput = document.getElementById('otp_code');
    const otpInputs = document.querySelectorAll('.otp-input-field');

    if (otpForm && otpCodeInput && otpInputs.length > 0) {
        // Auto-focus first input field
        otpInputs[0].focus();

        const updateOtpValue = () => {
            let code = '';
            otpInputs.forEach(input => {
                code += input.value;
            });
            otpCodeInput.value = code;
        };

        otpInputs.forEach((input, index) => {
            // Numeric validation and auto-advance
            input.addEventListener('input', (e) => {
                input.value = input.value.replace(/[^0-9]/g, '');
                if (input.value && index < otpInputs.length - 1) {
                    otpInputs[index + 1].focus();
                }
                updateOtpValue();
            });

            // Backspace navigation
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace') {
                    if (!input.value && index > 0) {
                        otpInputs[index - 1].value = '';
                        otpInputs[index - 1].focus();
                    } else {
                        input.value = '';
                    }
                    updateOtpValue();
                }
            });

            // Support pasting 6-digit codes
            input.addEventListener('paste', (e) => {
                const pasteData = e.clipboardData.getData('text').trim();
                if (/^\d{6}$/.test(pasteData)) {
                    pasteData.split('').forEach((char, i) => {
                        if (otpInputs[i]) {
                            otpInputs[i].value = char;
                        }
                    });
                    otpInputs[otpInputs.length - 1].focus();
                    updateOtpValue();
                }
                e.preventDefault();
            });
        });

        // Form Submission validation
        otpForm.addEventListener('submit', (e) => {
            updateOtpValue();
            if (otpCodeInput.value.length !== 6) {
                e.preventDefault();
                alert('Please enter a valid 6-digit OTP.');
            }
        });

        // Resend OTP Alert Trigger
        const resendBtn = document.getElementById('resendOtp');
        if (resendBtn) {
            resendBtn.addEventListener('click', (e) => {
                e.preventDefault();
                alert('A new OTP has been sent to your registered email address.');
            });
        }
    }
});
