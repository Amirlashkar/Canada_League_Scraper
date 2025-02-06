document.addEventListener("DOMContentLoaded", function () {
    const dropdown = document.getElementById("pperf");
    const plot = document.getElementById("PER_plot");

    dropdown.addEventListener("change", function () {
        const selectedValue = dropdown.value;

        // Send AJAX request to Django server
        fetch("/season/analytics/", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCSRFToken() // Ensure CSRF token is included
          },
          body: JSON.stringify({pperf_select: selectedValue})
        })
        .then(response => response.json())
        .then(data => {
            if (data.per_plot_div) {
                var perPlotData = JSON.parse(data.per_plot_div)
                var saccPlotData = JSON.parse(data.sacc_plot_div)
                Plotly.newPlot("PER_plot", perPlotData.data, perPlotData.layout);
                Plotly.newPlot("SACC_plot", saccPlotData.data, saccPlotData.layout);
            };
        })
        .catch(error => console.error("Error:", error));
    });

    function getCSRFToken() {
        return document.querySelector("[name=csrfmiddlewaretoken]").value;
    }
});
