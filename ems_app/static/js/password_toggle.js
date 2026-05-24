document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.querySelector('#password');
    const toggleBtn = document.querySelector('#toggle_password');
    const eyeOpen = document.querySelector('#eye_open');
    const eyeClosed = document.querySelector('#eye_closed');

    if (!passwordInput || !toggleBtn || !eyeOpen || !eyeClosed) return;

    toggleBtn.addEventListener('click', function() {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            eyeOpen.style.display = 'block';
            eyeClosed.style.display = 'none';
        } else {
            passwordInput.type = 'password';
            eyeOpen.style.display = 'none';
            eyeClosed.style.display = 'block';
        }
    });
});
