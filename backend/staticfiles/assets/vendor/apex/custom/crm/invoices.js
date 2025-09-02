var options = {
	chart: {
		height: 350,
		type: "area",
		toolbar: {
			show: false,
		},
	},
	dataLabels: {
		enabled: false,
	},
	stroke: {
		curve: "smooth",
		width: 3,
	},
	series: [
		{
			name: "Sales",
			data: [10, 40, 15, 40, 20, 35, 20, 10, 31, 43, 56, 29],
		},
		{
			name: "Revenue",
			data: [2, 8, 25, 7, 20, 20, 51, 35, 42, 20, 33, 67],
		},
	],
	grid: {
		borderColor: "#cccccc",
		strokeDashArray: 5,
		xaxis: {
			lines: {
				show: true,
			},
		},
		yaxis: {
			lines: {
				show: false,
			},
		},
		padding: {
			top: 0,
			right: 0,
			bottom: 10,
			left: 0,
		},
	},
	xaxis: {
		categories: [
			'Sent', 'Due', 'Overdue', 'Paid', 'Unpaid'
		],
	},
	yaxis: {
		labels: {
			show: false,
		},
	},
	colors: ["#501a92", "#999999","#9676be", "#a88dc9", "#b9a3d3", "#cbbade"],
	markers: {
		size: 0,
		opacity: 0.3,
		colors: ["#501a92", "#999999","#9676be", "#a88dc9", "#b9a3d3", "#cbbade"],
		strokeColor: "#ffffff",
		strokeWidth: 2,
		hover: {
			size: 7,
		},
	},
};

var chart = new ApexCharts(document.querySelector("#invoices"), options);

chart.render();
