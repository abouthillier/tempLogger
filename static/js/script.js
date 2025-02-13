//
//
//
const App = {
    $options: {
        // title: 'Temperature Over Time',
        curveType: 'function',
        legend: { position: 'bottom' },
        colors: ['#3b82f6', '#475569'],  // blue-500, slate-600
        backgroundColor: '#0f172a',       // slate-900
        chartArea: {
            width: '90%',
            height: '80%'
        },
        hAxis: {
            title: 'Most Recent Hour Of Data',
            titleTextStyle: { color: '#94a3b8' },  // slate-400
            textStyle: { color: '#94a3b8' }        // slate-400
        },
        vAxis: {
            // title: 'Temperature (°F)',
            titleTextStyle: { color: '#94a3b8' },  // slate-400
            textStyle: { color: '#94a3b8' },       // slate-400
            viewWindow: {
                min: 0,
                max: 800
            }
        },
        trendlines: {
            0: {
                type: 'linear',
                // // degree: 3,
                // opacity: 1,
                // lineWidth: 3,
                // color: '#8E44AD'
            }
        },
        explorer: {
            actions: ['dragToZoom', 'rightClickToReset'],
            axis: 'horizontal',
            keepInBounds: true,
            maxZoomIn: 4.0
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
        this.$dataTable.addColumn('number', 'Trend');

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
        const recentTemps = data.slice(-150);
        const minTemp = Math.min(...recentTemps);
        const maxTemp = Math.max(...recentTemps);
        return { min: minTemp, max: maxTemp };
    },

    updateChart(data) {
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

        const filteredData = data
            .filter(entry => new Date(entry.timestamp.replace(" ", "T")) >= oneHourAgo);

        const chartData = filteredData.map(entry => [
            entry.timestamp.split(" ")[1].slice(0, 5),
            parseFloat(entry.temperature),
            null
        ]);

        const recentTemps = filteredData.map(entry => entry.temperature);
        const latestTemp = recentTemps[recentTemps.length - 1];
        
        const tempTrending = this.getTempTrend(recentTemps);
        
        // Update temperature display and icon
        document.getElementById('currentStoveTemp').textContent = `${Math.floor(latestTemp)}°F`;
        document.getElementById('temp-up-icon').classList.toggle('hidden', tempTrending <= 0);
        document.getElementById('temp-down-icon').classList.toggle('hidden', tempTrending > 0);

        this.$dataTable.removeRows(0, this.$dataTable.getNumberOfRows());
        this.$dataTable.addRows(chartData);
        
        this.$chart.draw(this.$dataTable, this.$options);
    },
}

App.init();