var options = {
	chart: {
		height: 300,
		type: "bar",
		toolbar: {
			show: false,
		},
	},
	dataLabels: {
		enabled: false,
	},
	stroke: {
		width: 0,
	},
	series: [
		{
			name: "Income",
			data: [10, 20, 30, 40, 50, 30, 20],
		},
		{
			name: "Expenses",
			data: [8, 16, 24, 32, 42, 26, 12],
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
			"Mon",
			"Tue",
			"Wed",
			"Thu",
			"Fri",
			"Sat",
			"Sun",
		],
	},
	yaxis: {
		labels: {
			show: false,
		},
	},
	colors: ["#501a92", "#855fb3","#9676be", "#a88dc9", "#b9a3d3", "#cbbade"],
	markers: {
		size: 0,
		opacity: 0.3,
		colors: ["#501a92", "#855fb3","#9676be", "#a88dc9", "#b9a3d3", "#cbbade"],
		strokeColor: "#ffffff",
		strokeWidth: 2,
		hover: {
			size: 7,
		},
	},
};

var chart = new ApexCharts(document.querySelector("#income"), options);

chart.render();
