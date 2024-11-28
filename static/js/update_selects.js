$(document).ready(function() {
  function updateSelect(selectType, selectedValue) {
    const targetSelect = selectType === 'home' ? '#visitor' : '#home';

    $.ajax({
      url: '/update_selects/',
      data: { select_type: selectType, selected_value: selectedValue },
      success: function(response) {
        const options = response.options;
        if (options.length !== 0) {
          $(targetSelect).empty();

          options.forEach(function(option) {
            $(targetSelect).append(
                `<option value="${option.name}">${option.name}</option>`
            );
          });
        }
      },

      error: function() {
        alert('An error occurred while fetching the options.');
      }
    });
  }

  $('#home').change(function() {
    const selectedValue = $(this).val();
    updateSelect('home', selectedValue);
  });

  $('#visitor').change(function() {
    const selectedValue = $(this).val();
    updateSelect('visitor', selectedValue);
  });
})


