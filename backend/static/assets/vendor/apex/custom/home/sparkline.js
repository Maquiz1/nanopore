// Sparkline 1
var options1 = {
	series: [
		{
			name: "Clicks",
			data: [1, 2, 3, 2, 1],
		},
		{
			name: "Clicks",
			data: [1, 2, 3, 2, 1],
		},
	],
		chart: {
		type: "bar",
		height: 100,
		stacked: true,
		width: "100%",
		sparkline: {
			enabled: true,
		},
	},
	colors: ["#cccccc", "#ffffff"],
	stroke: {
		width: 0,
	},
	tooltip: {
		fixed: {
			enabled: false,
		},
		x: {
			show: false,
		},
		marker: {
			show: false,
		},
	},
	xaxis: {
		type: "day",
		categories: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
	},
	tooltip: {
		y: {
			formatter: function (val) {
				return val + "K";
			},
		},
	},
};
var chart1 = new ApexCharts(document.querySelector("#option1"), options1);
chart1.render();



// Sparkline 2
var options2 = {
	series: [
		{
			name: "Orders",
			data: [1, 2, 3, 2, 1],
		},
		{
			name: "Orders",
			data: [1, 2, 3, 2, 1],
		},
	],
		chart: {
		type: "bar",
		height: 100,
		stacked: true,
		width: "100%",
		sparkline: {
			enabled: true,
		},
	},
	colors: ["#cccccc", "#ffffff"],
	stroke: {
		width: 0,
	},
	tooltip: {
		fixed: {
			enabled: false,
		},
		x: {
			show: false,
		},
		marker: {
			show: false,
		},
	},
	xaxis: {
		type: "day",
		categories: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
	},
	tooltip: {
		y: {
			formatter: function (val) {
				return val + "K";
			},
		},
	},
};
var chart2 = new ApexCharts(document.querySelector("#option2"), options2);
chart2.render();




// Sparkline 3
var options3 = {
	series: [
		{
			name: "Income",
			data: [1, 2, 3, 2, 1],
		},
		{
			name: "Income",
			data: [1, 2, 3, 2, 1],
		},
	],
		chart: {
		type: "bar",
		height: 100,
		stacked: true,
		width: "100%",
		sparkline: {
			enabled: true,
		},
	},
	colors: ["#cccccc", "#ffffff"],
	stroke: {
		width: 0,
	},
	tooltip: {
		fixed: {
			enabled: false,
		},
		x: {
			show: false,
		},
		marker: {
			show: false,
		},
	},
	xaxis: {
		type: "day",
		categories: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
	},
	tooltip: {
		y: {
			formatter: function (val) {
				return val + "K";
			},
		},
	},
};
var chart3 = new ApexCharts(document.querySelector("#option3"), options3);
chart3.render();




// Sparkline 4
var options4 = {
	series: [
		{
			name: "Purchases",
			data: [1, 2, 3, 4, 5, 4, 3],
		},
		{
			name: "Purchases",
			data: [2, 3, 4, 5, 6, 5, 4],
		},
	],
		chart: {
		type: "bar",
		height: 50,
		width: 90,
		stacked: true,
		width: "100%",
		sparkline: {
			enabled: true,
		},
	},
	colors: ["#cccccc", "#548b0f"],
	stroke: {
		width: 0,
	},
	tooltip: {
		fixed: {
			enabled: false,
		},
		x: {
			show: false,
		},
		marker: {
			show: false,
		},
	},
	xaxis: {
		type: "day",
		categories: [
			"Monday",
			"Tuesday",
			"Wednesday",
			"Thursday",
			"Friday",
			"Saturday",
			"Sunday",
		],
	},
	tooltip: {
		y: {
			formatter: function (val) {
				return val + "K";
			},
		},
	},
};
var chart4 = new ApexCharts(document.querySelector("#option4"), options4);
chart4.render();






// Sparkline 5
var options5 = {
	series: [
		{
			name: "Purchases",
			data: [1, 2, 3, 4, 5, 6, 4],
		},
		{
			name: "Purchases",
			data: [2, 3, 4, 5, 6, 6, 3],
		},
	],
		chart: {
		type: "bar",
		height: 50,
		width: 90,
		stacked: true,
		width: "100%",
		sparkline: {
			enabled: true,
		},
	},
	colors: ["#cccccc", "#2d3ebc"],
	stroke: {
		width: 0,
	},
	tooltip: {
		fixed: {
			enabled: false,
		},
		x: {
			show: false,
		},
		marker: {
			show: false,
		},
	},
	xaxis: {
		type: "day",
		categories: [
			"Monday",
			"Tuesday",
			"Wednesday",
			"Thursday",
			"Friday",
			"Saturday",
			"Sunday",
		],
	},
	tooltip: {
		y: {
			formatter: function (val) {
				return val + "K";
			},
		},
	},
};
var chart5 = new ApexCharts(document.querySelector("#option5"), options5);
chart5.render();






// Sparkline 6
var options6 = {
	series: [
		{
			name: "Purchases",
			data: [1, 2, 3, 4, 5, 6, 5],
		},
		{
			name: "Purchases",
			data: [2, 3, 4, 5, 6, 7, 4],
		},
	],
		chart: {
		type: "bar",
		height: 50,
		width: 90,
		stacked: true,
		width: "100%",
		sparkline: {
			enabled: true,
		},
	},
	colors: ["#cccccc", "#e1204d"],
	stroke: {
		width: 0,
	},
	tooltip: {
		fixed: {
			enabled: false,
		},
		x: {
			show: false,
		},
		marker: {
			show: false,
		},
	},
	xaxis: {
		type: "day",
		categories: [
			"Monday",
			"Tuesday",
			"Wednesday",
			"Thursday",
			"Friday",
			"Saturday",
			"Sunday",
		],
	},
	tooltip: {
		y: {
			formatter: function (val) {
				return val + "K";
			},
		},
	},
};
var chart6 = new ApexCharts(document.querySelector("#option6"), options6);
chart6.render();
