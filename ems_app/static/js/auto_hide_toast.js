document.addEventListener('DOMContentLoaded', () => {
    const toast = document.getElementById('toast-notification');

    if (toast) {
        setTimeout(() => {
            toast.classList.remove('opacity-0');
            toast.classList.add('opacity-100');
        }, 100);


        setTimeout(() => {
            toast.classList.remove('opacity-100');
            toast.classList.add('opacity-0');
            setTimeout(() => {
                toast.style.display = 'none';
            }, 500);

        }, 4000);
    }
});
