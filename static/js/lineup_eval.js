function createDateDropdown(parentId, yearId, yearInputId, monthId, monthInputId, dayId, dayInputId) {
    // create year dropdown
    const year = document.createElement('select');
    year.id = yearId;
    for (let i = new Date().getFullYear(); i > 2010; i--) {
        let option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        year.appendChild(option);
    }

    // create month dropdown
    const month = document.createElement('select');
    month.id = monthId;
    for (let i = 1; i <= 12; i++) {
        let option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        month.appendChild(option);
    }

    // create day dropdown
    const day = document.createElement('select');
    day.id = dayId;

    function populateDays() {
        const selectedYear = year.value;
        const selectedMonth = month.value;
        const selectedDay = day.value;
        const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();

        day.innerHTML = '';
        for (let i = 1; i <= daysInMonth; i++) {
            let option = document.createElement('option');
            option.value = i;
            option.textContent = i;
            day.appendChild(option);
        }

        // If previously selected day is in the new month range, preserve it
        if (selectedDay.trim() === "") {
            day.value = 1;
        } else {
            if (selectedDay > daysInMonth) {
                day.value = daysInMonth;
            } else {
                day.value = selectedDay;
            }
        }
    };

    year.addEventListener('change', () => {
        populateDays();
        document.getElementById(yearInputId).value = year.value;
    });
    month.addEventListener('change', () => {
        populateDays();
        document.getElementById(monthInputId).value = month.value;
    });
    day.addEventListener('change', () => {
        document.getElementById(dayInputId).value = day.value;
    });

    populateDays();

    document.getElementById(yearInputId).value = year.value;
    document.getElementById(monthInputId).value = month.value;
    document.getElementById(dayInputId).value = day.value;

    // add dropdowns to parent element
    const parent = document.getElementById(parentId);
    parent.appendChild(month);
    parent.appendChild(day);
    parent.appendChild(year);
}

createDateDropdown('match-date', 'match-year', 'match-year-input', 
'match-month', 'match-month-input', 'match-day', 'match-day-input');
