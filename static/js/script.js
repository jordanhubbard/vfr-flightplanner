// Initialize the map
let map = L.map('map').setView([37.7749, -122.4194], 8);

// If initial coordinates are provided, use them
if (initialLat !== null && initialLon !== null) {
    map.setView([initialLat, initialLon], 10);
    // Trigger weather fetch for initial location
    fetchWeatherData(initialLat, initialLon);
    updateSelectedLocation(initialLat, initialLon);
}

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// API Status elements
const owmStatus = document.getElementById('owm-status');
const meteoStatus = document.getElementById('meteo-status');
const owmIndicator = document.getElementById('owm-indicator');
const meteoIndicator = document.getElementById('meteo-indicator');
const owmErrorMessage = document.getElementById('owm-error-message');
const meteoErrorMessage = document.getElementById('meteo-error-message');
const owmLastCheck = document.getElementById('owm-last-check');
const meteoLastCheck = document.getElementById('meteo-last-check');
const owmCalls = document.getElementById('owm-calls');

// Function to format timestamp
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

// Function to update API status indicators
function updateApiStatus() {
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            // Update OpenWeatherMap status
            owmStatus.className = `status-dot ${data.openweathermap.status ? 'online' : 'offline'}`;
            if (!data.openweathermap.status) {
                owmErrorMessage.textContent = data.openweathermap.error || 'Unknown error';
                owmIndicator.classList.add('show-error');
            } else {
                owmErrorMessage.textContent = 'No errors reported';
                owmIndicator.classList.remove('show-error');
            }
            owmLastCheck.textContent = `Last checked: ${formatTimestamp(data.openweathermap.timestamp)}`;
            owmCalls.textContent = `API calls: ${data.openweathermap.api_calls}`;
            
            // Update Open-Meteo status
            meteoStatus.className = `status-dot ${data.openmeteo.status ? 'online' : 'offline'}`;
            if (!data.openmeteo.status) {
                meteoErrorMessage.textContent = data.openmeteo.error || 'Unknown error';
                meteoIndicator.classList.add('show-error');
            } else {
                meteoErrorMessage.textContent = 'No errors reported';
                meteoIndicator.classList.remove('show-error');
            }
            meteoLastCheck.textContent = `Last checked: ${formatTimestamp(data.openmeteo.timestamp)}`;
        })
        .catch(error => {
            console.error('Error checking API health:', error);
            // If we can't reach our backend, mark both as offline with error messages
            owmStatus.className = 'status-dot offline';
            meteoStatus.className = 'status-dot offline';
            
            const errorMessage = 'Cannot connect to application server';
            owmErrorMessage.textContent = errorMessage;
            meteoErrorMessage.textContent = errorMessage;
            
            owmIndicator.classList.add('show-error');
            meteoIndicator.classList.add('show-error');
            
            const timestamp = new Date().toLocaleString();
            owmLastCheck.textContent = `Last checked: ${timestamp}`;
            meteoLastCheck.textContent = `Last checked: ${timestamp}`;
        });
}

// Add click handlers to toggle error details on mobile
owmIndicator.addEventListener('click', function() {
    this.classList.toggle('show-error');
});

meteoIndicator.addEventListener('click', function() {
    this.classList.toggle('show-error');
});

// Check API status immediately and then every 30 seconds
updateApiStatus();
setInterval(updateApiStatus, 30000);

// Initialize variables
let currentMarker = null;
let lastKnownPosition = null;
let airportMarkers = [];  // Array to store airport markers
const daysSlider = document.getElementById('forecast-days');
const daysValue = document.getElementById('days-value');
const opacitySlider = document.getElementById('overlay-opacity');
const maxForecastDays = 16;  // Open-Meteo API limitation
const airportCodeInput = document.getElementById('airport-code');
const goAirportButton = document.getElementById('go-airport');

// Weather overlay layers
let weatherLayers = {
    clouds: L.tileLayer(`https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: '© OpenWeatherMap',
        opacity: 0.7
    }),
    precipitation: L.tileLayer(`https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: '© OpenWeatherMap',
        opacity: 0.7
    }),
    wind: L.tileLayer(`https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: '© OpenWeatherMap',
        opacity: 0.7
    }),
    temp: L.tileLayer(`https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: '© OpenWeatherMap',
        opacity: 0.7
    })
};

// Weather codes mapping
const weatherCodes = {
    0: 'Clear sky',
    1: 'Mainly clear',
    2: 'Partly cloudy',
    3: 'Overcast',
    45: 'Foggy',
    48: 'Depositing rime fog',
    51: 'Light drizzle',
    53: 'Moderate drizzle',
    55: 'Dense drizzle',
    61: 'Slight rain',
    63: 'Moderate rain',
    65: 'Heavy rain',
    71: 'Slight snow',
    73: 'Moderate snow',
    75: 'Heavy snow',
    77: 'Snow grains',
    80: 'Slight rain showers',
    81: 'Moderate rain showers',
    82: 'Violent rain showers',
    85: 'Slight snow showers',
    86: 'Heavy snow showers',
    95: 'Thunderstorm',
    96: 'Thunderstorm with slight hail',
    99: 'Thunderstorm with heavy hail'
};

// Function to get weather description from code
function getWeatherDescription(code) {
    return weatherCodes[code] || 'Unknown';
}

// Update days value display and refresh data
daysSlider.addEventListener('input', function() {
    const days = parseInt(this.value);
    daysValue.textContent = days;
    
    // Fetch weather data
    fetchWeatherData();
});

// Handle map clicks
map.on('click', (e) => {
    lastKnownPosition = e.latlng;
    
    // Update or create marker
    if (currentMarker) {
        currentMarker.setLatLng(lastKnownPosition);
    } else {
        currentMarker = L.marker(lastKnownPosition).addTo(map);
    }
    
    // Update location text
    const locationText = document.getElementById('selected-location');
    locationText.textContent = `Selected Location: ${lastKnownPosition.lat.toFixed(4)}°N, ${lastKnownPosition.lng.toFixed(4)}°W`;
    
    // Get weather data for the location
    fetchWeatherData();
    
    // Fetch airports if the overlay is enabled
    if (overlayCheckboxes.airports.checked) {
        fetchAirports(lastKnownPosition.lat, lastKnownPosition.lng);
    }
});

// Function to fetch and display airports
async function fetchAirports(lat, lon) {
    try {
        const response = await fetch('/get_airports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                radius: 50  // 50km radius
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch airports');
        }
        
        const data = await response.json();
        
        // Clear existing airport markers
        airportMarkers.forEach(marker => map.removeLayer(marker));
        airportMarkers = [];
        
        // Add new airport markers
        data.airports.forEach(airport => {
            const marker = L.marker([airport.lat, airport.lon])
                .bindPopup(`
                    <strong>${airport.name}</strong><br>
                    ${airport.iata ? `IATA: ${airport.iata}` : ''}<br>
                    ${airport.icao ? `ICAO: ${airport.icao}` : ''}<br>
                    Type: ${airport.type}
                `);
            
            // Only add to map if airports overlay is checked
            if (overlayCheckboxes.airports.checked) {
                marker.addTo(map);
            }
            
            airportMarkers.push(marker);
        });
    } catch (error) {
        console.error('Error fetching airports:', error);
    }
}

// Handle overlay checkboxes with automatic refresh
const overlayCheckboxes = {
    clouds: document.getElementById('clouds-overlay'),
    precipitation: document.getElementById('precipitation-overlay'),
    wind: document.getElementById('wind-overlay'),
    temp: document.getElementById('temp-overlay'),
    airports: document.getElementById('airports-overlay')
};

// Add event listeners to all checkboxes
Object.entries(overlayCheckboxes).forEach(([type, checkbox]) => {
    checkbox.addEventListener('change', (e) => {
        if (type === 'airports') {
            if (e.target.checked && lastKnownPosition) {
                // If airports are being enabled, fetch and show them
                fetchAirports(lastKnownPosition.lat, lastKnownPosition.lng);
            } else {
                // If airports are being disabled, remove all markers
                airportMarkers.forEach(marker => map.removeLayer(marker));
            }
        } else {
            toggleOverlay(type, e.target.checked);
            fetchWeatherData();
        }
    });
});

// Handle opacity changes
opacitySlider.addEventListener('input', (e) => {
    const opacity = e.target.value / 100;
    Object.values(weatherLayers).forEach(layer => {
        if (map.hasLayer(layer)) {
            layer.setOpacity(opacity);
        }
    });
});

// Update the toggle overlay function
function toggleOverlay(type, show) {
    if (show) {
        weatherLayers[type].addTo(map);
        weatherLayers[type].setOpacity(opacitySlider.value / 100);
    } else {
        weatherLayers[type].remove();
    }
}

// Function to refresh weather data
async function fetchWeatherData() {
    if (!lastKnownPosition) {
        return;
    }
    
    try {
        const days = parseInt(daysSlider.value);
        
        const response = await fetch('/get_weather', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lat: lastKnownPosition.lat,
                lon: lastKnownPosition.lng,
                days: Math.min(days, maxForecastDays),  // Ensure we don't exceed the API limit
                overlays: Object.entries(overlayCheckboxes)
                    .filter(([_, checkbox]) => checkbox.checked)
                    .map(([type]) => type)
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.details || errorData.error || 'Failed to fetch weather data');
        }
        
        const data = await response.json();
        displayWeatherData(data);
    } catch (error) {
        console.error('Error fetching weather data:', error);
        const container = document.getElementById('forecast-container');
        container.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

// Display weather data in the forecast container
function displayWeatherData(data) {
    const container = document.getElementById('forecast-container');
    container.innerHTML = '';
    
    // Create table header
    const table = document.createElement('table');
    table.className = 'forecast-table';
    
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Date</th>
            <th>Conditions</th>
            <th>Temperature</th>
            <th>Wind</th>
            <th>Visibility</th>
            <th>Clouds</th>
            <th>Pressure</th>
        </tr>
    `;
    table.appendChild(thead);
    
    // Create table body
    const tbody = document.createElement('tbody');
    
    // Process each day's data
    data.daily.time.forEach((date, index) => {
        const row = document.createElement('tr');
        
        // Format date
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });
        
        // Get weather description
        const weatherCode = data.daily.weathercode[index];
        const weatherDesc = getWeatherDescription(weatherCode);
        
        // Format temperature
        const tempMax = data.daily.temperature_2m_max[index];
        const tempMin = data.daily.temperature_2m_min[index];
        const tempStr = `${Math.round(tempMax)}°F / ${Math.round(tempMin)}°F`;
        
        // Format wind (including direction and gusts)
        const windSpeed = data.daily.windspeed_10m_max[index];
        const windDir = data.daily.winddirection_10m_dominant[index];
        const windGust = data.daily.windgusts_10m_max[index];
        
        // Calculate wind trend
        let windTrend = '';
        if (index > 0) {
            const prevWindGust = data.daily.windgusts_10m_max[index - 1];
            const gustDiff = windGust - prevWindGust;
            if (Math.abs(gustDiff) > 5) {  // Only show trend if change is significant
                windTrend = gustDiff > 0 ? '↑' : '↓';
            }
        }
        
        // Add wind advisory if gusts are significant
        let windAdvisory = '';
        if (windGust > 25) {
            windAdvisory = '<span class="wind-advisory">Strong winds expected</span>';
        }
        
        const windStr = `${Math.round(windSpeed)}kt ${Math.round(windDir)}°${windGust ? ` (${Math.round(windGust)}kt gusts${windTrend})` : ''} ${windAdvisory}`;
        
        // Format visibility (convert meters to miles)
        const visibility = data.daily.visibility_mean[index];
        const visibilityMiles = (visibility / 1609.34).toFixed(1);  // Convert meters to miles
        const visibilityStr = `${visibilityMiles}mi`;
        
        // Format cloud cover
        const cloudCover = data.daily.cloudcover_mean[index];
        const cloudStr = `${Math.round(cloudCover)}%`;
        
        // Format pressure (altimeter setting)
        const pressure = data.daily.pressure[index] || 29.92;  // Default to standard pressure if not available
        const pressureStr = `${pressure.toFixed(2)}" Hg`;
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td>${weatherDesc}</td>
            <td>${tempStr}</td>
            <td>${windStr}</td>
            <td>${visibilityStr}</td>
            <td>${cloudStr}</td>
            <td>${pressureStr}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
    container.appendChild(table);
}

// Add event listener for airport code search
goAirportButton.addEventListener('click', handleAirportSearch);
airportCodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleAirportSearch();
    }
});

// Function to handle airport code search
async function handleAirportSearch() {
    const airportCode = airportCodeInput.value.trim().toUpperCase();
    if (!airportCode) return;

    try {
        const response = await fetch('/get_airport_coordinates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                airport_code: airportCode
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.details || errorData.error || 'Failed to fetch airport coordinates');
        }

        const data = await response.json();
        
        // Update map view and marker
        map.setView([data.lat, data.lon], 10);
        lastKnownPosition = { lat: data.lat, lng: data.lon };
        
        if (currentMarker) {
            currentMarker.setLatLng(lastKnownPosition);
        } else {
            currentMarker = L.marker(lastKnownPosition).addTo(map);
        }

        // Update location text
        const locationText = document.getElementById('selected-location');
        locationText.textContent = `${airportCode}: ${data.lat.toFixed(4)}°N, ${data.lon.toFixed(4)}°W`;

        // Fetch weather data
        fetchWeatherData();

        // Clear the input
        airportCodeInput.value = '';
    } catch (error) {
        console.error('Error fetching airport coordinates:', error);
        const container = document.getElementById('forecast-container');
        container.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
} 