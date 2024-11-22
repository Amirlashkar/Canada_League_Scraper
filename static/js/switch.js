document.addEventListener('DOMContentLoaded', function() {
    var statusElement = document.getElementById('dynamic_pl');
    var inputElement = document.getElementById('pl');

    // Function to update the input value
    function updateInputValue() {
        if (statusElement.classList.contains('on')) {
            inputElement.value = 'Lineups';
        } else if (statusElement.classList.contains('off')) {
            inputElement.value = 'Players';
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

document.addEventListener('DOMContentLoaded', function() {
    var statusElement = document.getElementById('dynamic_hv');
    var inputElement = document.getElementById('hv');

    // Function to update the input value
    function updateInputValue() {
        if (statusElement.classList.contains('on')) {
            inputElement.value = 'Visitor';
        } else if (statusElement.classList.contains('off')) {
            inputElement.value = 'Home';
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

document.addEventListener('DOMContentLoaded', function() {
    var statusElement = document.getElementById('dynamic_mw');
    var inputElement = document.getElementById('mw');

    // Function to update the input value
    function updateInputValue() {
        if (statusElement.classList.contains('on')) {
            inputElement.value = 'women';
        } else if (statusElement.classList.contains('off')) {
            inputElement.value = 'men';
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
