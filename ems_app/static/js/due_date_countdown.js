// FEATURE: Live "due in X days" countdown.
// OVERDUE = oxblood (danger). Everything else = mustard (warning).

document.addEventListener('DOMContentLoaded', () => {
    // grab every element that holds a due date (there can be many on the page)
    const badges = document.querySelectorAll('.due-badge');

    // if there are none on this page, stop here
    if (badges.length === 0) return;

    // today's date, with the time part removed so we compare whole days only
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // go through each badge one by one
    badges.forEach((badge) => {
        // read the due date we stored on the element as data-due (format: 2025-05-30)
        const due = new Date(badge.dataset.due);

        // how many whole days between today and the due date
        const oneDay = 1000 * 60 * 60 * 24;
        const daysLeft = Math.round((due - today) / oneDay);

        // decide the message and color based on how many days are left
        if (daysLeft < 0) {
            badge.textContent = 'OVERDUE';
            badge.style.color = '#842424'; // oxblood — danger
        } else if (daysLeft === 0) {
            badge.textContent = 'Due today';
            badge.style.color = '#654505'; // mustard — warning
        } else {
            badge.textContent = daysLeft + ' day(s) left';
            badge.style.color = '#654505'; // mustard — warning
        }
    });
});
