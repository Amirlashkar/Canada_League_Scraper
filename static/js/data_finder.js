function createDateDropdown(parentId, yearId, yearInputId, monthId, monthInputId, dayId, dayInputId) {
   // create year dropdown
   const year = document.createElement('select');
   year.id = yearId;
   for (let i = new Date().getFullYear(); i > 1900; i--) {
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
       const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
       
       day.innerHTML = '';
       for (let i = 1; i <= daysInMonth; i++) {
       let option = document.createElement('option');
       option.value = i;
       option.textContent = i;
       day.appendChild(option);
       }
       
       // update hidden inputs with selected date values
       document.getElementById(yearInputId).value = selectedYear;
       document.getElementById(monthInputId).value = selectedMonth;
       document.getElementById(dayInputId).value = day.value;
   }
   
   year.addEventListener('change', populateDays);
   month.addEventListener('change', populateDays);
   day.addEventListener('change', () => {
       document.getElementById(dayInputId).value = day.value;
   });
   
   populateDays();
   
   // add dropdowns to parent element
   const parent = document.getElementById(parentId);
   parent.appendChild(month);
   parent.appendChild(day);
   parent.appendChild(year);
}

createDateDropdown('start-date', 'start-year', 'start-year-input', 
'start-month', 'start-month-input', 'start-day', 'start-day-input');
createDateDropdown('end-date', 'end-year', 'end-year-input', 
'end-month', 'end-month-input', 'end-day', 'end-day-input');
