document.addEventListener('DOMContentLoaded', function() {
    var statusElement = document.getElementById('dynamic');
    var inputElement = document.getElementById('switch');

    // Function to update the input value
    function updateInputValue() {
        if (statusElement.classList.contains('on')) {
            inputElement.value = 'lineups';
        } else if (statusElement.classList.contains('off')) {
            inputElement.value = 'players';
        }
    }

    // Create a MutationObserver to watch for changes
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                updateInputValue();
            }
        });
    });

    // Start observing
    observer.observe(statusElement, {
        attributes: true //configure it to listen to attribute changes
    });
});
