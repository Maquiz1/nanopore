var options = {
	chart: {
	  height: 350,
	  width: '100%',
	  type: 'bar',
	  toolbar: {
		show: false,
	  },
	},
	plotOptions: {
	  bar: {
		horizontal: false,
		columnWidth: '40%',
		borderRadius: 3,
	  },
	},
	dataLabels: {
	  enabled: false
	},
	stroke: {
	  show: true,
	  width: 0,
	  colors: ["#501a92", "#7348a8", "#9676be", "#b9a3d3","#dcd1e9", "#eee8f4"]
	},
	series: [{
	  name: 'Projects',
	  data: [14, 10, 8, 2, 3, 5, 4]
	}],
	legend: {
	  show: false,
	},
	xaxis: {
	  categories: ['Total', 'Not Started', 'In Progress', 'On Hold', 'Cancelled', 'Finished', 'Pending'],
	},
	yaxis: {
	  show: false,
	},
	fill: {
	  colors: ["#501a92", "#7348a8", "#9676be", "#b9a3d3","#dcd1e9", "#eee8f4"],
	},
	tooltip: {
	  y: {
		formatter: function(val) {
		  return + val
		}
	  }
	},
	grid: {
	  show: false,
	  xaxis: {
		lines: {
		  show: true
		}
	  },   
	  yaxis: {
		lines: {
		  show: false,
		} 
	  },
	},
	colors: ['#ffffff'],
  }
  var chart = new ApexCharts(
	document.querySelector("#projects"),
	options
  );
chart.render();
  


















