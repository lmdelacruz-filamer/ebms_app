// FEATURE: Real-time greeting.
// Reads the computer's current hour and shows "Good morning / afternoon / evening"
// with a short message. Morning = before 12, afternoon = 12 to 17, evening = 18 onward.

document.addEventListener('DOMContentLoaded', () => {
    // grab the two empty elements we will fill, by their id
    const greetingEl = document.querySelector('#greeting');
    const subEl = document.querySelector('#greeting_sub');

    // if they aren't on this page, stop here
    if (!greetingEl) return;

    // read the operator's name we stored on the element as data-name
    const name = greetingEl.dataset.name || 'Operator';

    // get the current hour from the computer's clock (0 to 23)
    const hour = new Date().getHours();

    // decide the greeting word and message based on the hour
    let greeting;
    let message;
    if (hour < 12) {
        greeting = 'Good morning';
        message = 'The yard is fresh — let\u2019s get the equipment moving.';
    } else if (hour < 18) {
        greeting = 'Good afternoon';
        message = 'Midday check — keep the loans and returns on track.';
    } else {
        greeting = 'Good evening';
        message = 'Winding down — review what\u2019s still out before you log off.';
    }

    // put the finished greeting and message onto the page
    greetingEl.textContent = greeting + ', ' + name;
    if (subEl) subEl.textContent = message;
});
