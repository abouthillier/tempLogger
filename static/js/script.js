//
//
//
const App = {
    $options: {
        // title: 'Temperature Over Time',
        curveType: 'function',
        legend: 'none',
        colors: ['#3b82f6'],
        backgroundColor: '#0f172a',       // slate-900
        chartArea: {
            width: '90%',
            height: '80%'
        },
        hAxis: {
            // title: 'Most Recent Hour Of Data',
            // titleTextStyle: { color: '#94a3b8' },  // slate-400
            // textStyle: { color: '#94a3b8' }        // slate-400
        },
        vAxis: {
            textStyle: { color: '#94a3b8' },  // slate-400
            viewWindow: {
                min: 0,
                max: 800
            }
        },
        series: {
            0: {
                // Main series configuration
                color: '#3b82f6'
            }
        },
        trendlines: {
            0: {
                type: 'polynomial',
                degree: 5,
                opacity: 0.8,
                lineWidth: 5,
                labelInLegend: 'Trend',
                color: '#FFD22F' // amber-300
            }
        }
    },
    $dataTable: null,
    $chart: null,

    init() {
        google.charts.load('current', {'packages':['corechart']});
        google.charts.setOnLoadCallback(() => this.initChart());
    },

    initChart() {
        this.$dataTable = new google.visualization.DataTable();
        this.$dataTable.addColumn('string', 'Time');
        this.$dataTable.addColumn('number', 'Temperature');

        this.$chart = new google.visualization.LineChart(document.getElementById('temperatureChart'));
        
        setInterval(() => this.fetchCSVData(), 2000);
    },

    getTempTrend(data) {
        const recentTemps = data.slice(-150);
        const n = recentTemps.length;
        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    
        for (let i = 0; i < n; i++) {
            sumX += i;
            sumY += recentTemps[i];
            sumXY += i * recentTemps[i];
            sumX2 += i * i;
        }
    
        const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
        return slope;
    },

    async fetchCSVData() {
        try {
            // First, get all responses
            const responses = await Promise.all([
                fetch('/get_csv_json'),
                fetch('/temps')
            ]);

            // Check if all responses are ok
            if (!responses.every(response => response.ok)) {
                throw new Error('One or more network responses failed');
            }

            // Then parse the responses
            const data = await responses[0].json();
            const sysTemps = await responses[1].json();

            // TODO: Uncomment this when Nest data is available
            // await this.fetchNestData();

            // Validate data
            if (data.error || !Array.isArray(data)) {
                throw new Error("Invalid temperature data received");
            }

            if (!sysTemps || typeof sysTemps.cpu_temp === 'undefined' || typeof sysTemps.gpu_temp === 'undefined') {
                throw new Error("Invalid system temperature data received");
            }

            // Update system temperatures
            const cpuTempElement = document.getElementById('cpu-temp');
            const gpuTempElement = document.getElementById('gpu-temp');
            
            if (cpuTempElement && gpuTempElement) {
                cpuTempElement.innerText = Math.round(sysTemps.cpu_temp);
                gpuTempElement.innerText = Math.round(sysTemps.gpu_temp);
            }

            const recentTemps = data.map(entry => entry.temperature);
            const latestTemp = recentTemps[recentTemps.length - 1];
            
            const tempTrending = this.getTempTrend(recentTemps);
            
            // Update temperature display and icon
            document.getElementById('currentStoveTemp').textContent = Math.floor(latestTemp);
            document.getElementById('temp-up-icon').classList.toggle('hidden', tempTrending <= 0);
            document.getElementById('temp-down-icon').classList.toggle('hidden', tempTrending > 0);
    
            // Update chart with validated data
            this.updateChart(data);

        } catch (error) {
            console.error('Error fetching data:', error.message);
            // Optionally show error to user
            const errorElement = document.getElementById('error-message');
            if (errorElement) {
                errorElement.textContent = 'Failed to update temperature data';
            }
        }
    },

    async fetchNestData() {
        let nestTemps = [];

        try {
            const response = await fetch('/nest_temperatures');
            nestTemps = await response.json();
            
            const nestTempsElement = document.getElementById('nest-temps');
            // Update Nest temperatures
            if (nestTempsElement && Array.isArray(nestTemps)) {
                nestTempsElement.innerHTML = nestTemps
                    .map(temp => `${temp.name}: ${temp.temperature}°F`)
                    .join(' | ');
            }
        } catch (error) {
            console.error('Error fetching Nest data:', error);
        }
    },

    determineBounds(data) {

        const temps = data.map(entry => entry.temperature);
        const minTemp = Math.min(...temps);
        const maxTemp = Math.max(...temps);
        this.$options.vAxis.viewWindow.min = minTemp;
        this.$options.vAxis.viewWindow.max = maxTemp;
    },

    updateChart(data) {
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

        const filteredData = data
            .filter(entry => new Date(entry.timestamp.replace(" ", "T")) >= oneHourAgo);

        // Convert timestamps to numbers (minutes since start) for better trendline calculation
        const startTime = new Date(filteredData[0].timestamp.replace(" ", "T")).getTime();
        const chartData = filteredData.map(entry => {
            const time = entry.timestamp.split(" ")[1].slice(0, 5);
            const temp = parseFloat(entry.temperature);
            const minutesSinceStart = ((new Date(entry.timestamp.replace(" ", "T")).getTime() - startTime) / (1000 * 60)) - 60;
            return [minutesSinceStart, temp];
        });

        // Update DataTable with numeric X values
        this.$dataTable = new google.visualization.DataTable();
        this.$dataTable.addColumn('number', 'Minutes');  // Changed to number type
        this.$dataTable.addColumn('number', 'Temperature');
        this.$dataTable.addRows(chartData);

        this.determineBounds(filteredData);

        // Format the axis to show time labels
        const formatter = new google.visualization.NumberFormat({pattern: '#.#'});
        formatter.format(this.$dataTable, 0);

        this.$chart.draw(this.$dataTable, this.$options);
    },
}

App.init();