var options = {
	chart: {
		width: 310,
		type: "donut",
	},
	labels: ["Open", "Progress", "Closed"],
	series: [20, 45, 65],
	legend: {
		position: "bottom",
	},
	dataLabels: {
		enabled: false,
	},
	stroke: {
		width: 0,
	},
	colors: ["#501a92", "#7348a8", "#9676be", "#b9a3d3","#dcd1e9", "#eee8f4"],
};
var chart = new ApexCharts(document.querySelector("#tickets"), options);
chart.render();
