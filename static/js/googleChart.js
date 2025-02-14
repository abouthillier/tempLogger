// const googleChart = {

//     init () {

//         google.charts.load('current', {'packages':['corechart']});

//         // Set a callback to run when the Google Visualization API is loaded.
//         google.charts.setOnLoadCallback(drawChart);
    
//     };

//     // Callback that creates and populates a data table,
//     // instantiates the pie chart, passes in the data and
//     // draws it.
//     drawChart () {
//         var data = google.visualization.arrayToDataTable([
//           ['Year', 'Sales', 'Expenses'],
//           ['2004',  1000,      400],
//           ['2005',  1170,      460],
//           ['2006',  660,       1120],
//           ['2007',  1030,      540]
//         ]);

//         var options = {
//           curveType: 'function',
//           legend: { position: 'bottom' }
//         };

//         var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

//         chart.draw(data, options);
//     };

// };

// googleChart.init();