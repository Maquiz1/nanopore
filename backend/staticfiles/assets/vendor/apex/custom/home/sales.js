var options = {
          series: [
          {
            name: "",
            data: [200, 330, 548, 740, 880, 1100, 1380],
          },
        ],
          chart: {
          type: 'bar',
            height: 300,
          toolbar: {
			show: false,
		},
        },
        dataLabels: {
		enabled: false,
	},
        plotOptions: {
          bar: {
            borderRadius: 0,
            horizontal: true,
            distributed: true,
            barHeight: '80%',
            isFunnel: true,
          },
        },
        colors: [
          "#501a92", "#62319d", "#7348a8", "#855fb3","#9676be", "#a88dc9", "#b9a3d3", "#cbbade"
        ],
        dataLabels: {
          enabled: true,
          formatter: function (val, opt) {
            return opt.w.globals.labels[opt.dataPointIndex] 
          },
          dropShadow: {
            enabled: true,
          },
        },
        xaxis: {
          categories: ['Sweets', 'Meat', 'Dairy', 'Processed Foods', 'Healthy Fats', 'Fruits & Vegetables', 'Grains'],
        },
        legend: {
          show: false,
        },
        };

        var chart = new ApexCharts(document.querySelector("#sales"), options);
        chart.render();