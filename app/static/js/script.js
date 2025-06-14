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

// --- Flight Planner UI ---
const flightPlanForm = document.getElementById('flight-plan-form');
const fromAirportInput = document.getElementById('from-airport');
const toAirportInput = document.getElementById('to-airport');
const aircraftRangeInput = document.getElementById('aircraft-range');
const groundspeedInput = document.getElementById('groundspeed');
const routeSummaryDiv = document.getElementById('route-summary');
let routePolyline = null;
let fuelStopMarkers = [];

flightPlanForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    // Clear previous route
    if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
    }
    fuelStopMarkers.forEach(marker => map.removeLayer(marker));
    fuelStopMarkers = [];
    routeSummaryDiv.innerHTML = '';

    const from = fromAirportInput.value.trim().toUpperCase();
    const to = toAirportInput.value.trim().toUpperCase();
    const range = parseFloat(aircraftRangeInput.value);
    const groundspeed = parseFloat(groundspeedInput.value);
    if (!from || !to || isNaN(range) || isNaN(groundspeed)) {
        routeSummaryDiv.innerHTML = '<div class="error-message">All fields are required.</div>';
        return;
    }
    try {
        routeSummaryDiv.innerHTML = 'Planning route...';
        const response = await fetch('/api/plan_route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from, to, range, groundspeed })
        });
        const data = await response.json();
        if (!response.ok || data.error) {
            routeSummaryDiv.innerHTML = `<div class="error-message">${data.error || 'Failed to plan route.'}</div>`;
            return;
        }
        // Draw route polyline
        const legs = data.legs;
        if (!legs || legs.length === 0) {
            routeSummaryDiv.innerHTML = '<div class="error-message">No route found.</div>';
            return;
        }
        // Fetch coordinates for each airport in the route
        const airportCoords = {};
        const airportInfo = {};
        for (const leg of legs) {
            if (!airportCoords[leg.from]) {
                const res = await fetch(`/api/airport?code=${leg.from}`);
                const info = await res.json();
                airportCoords[leg.from] = [info.latitude, info.longitude];
                airportInfo[leg.from] = info;
            }
            if (!airportCoords[leg.to]) {
                const res = await fetch(`/api/airport?code=${leg.to}`);
                const info = await res.json();
                airportCoords[leg.to] = [info.latitude, info.longitude];
                airportInfo[leg.to] = info;
            }
        }
        // Fetch weather for each waypoint
        const weatherByCode = {};
        for (const code of Object.keys(airportCoords)) {
            const [lat, lon] = airportCoords[code];
            const wres = await fetch('/api/weather', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat, lon, days: 1 })
            });
            const wdata = await wres.json();
            weatherByCode[code] = wdata.current || {};
        }
        // Build polyline coordinates
        const routeCoords = [airportCoords[legs[0].from]];
        legs.forEach(leg => routeCoords.push(airportCoords[leg.to]));
        routePolyline = L.polyline(routeCoords, { color: 'blue', weight: 4 }).addTo(map);
        map.fitBounds(routePolyline.getBounds(), { padding: [50, 50] });
        // Mark fuel stops (all intermediate airports)
        data.fuel_stops.forEach(code => {
            const [lat, lon] = airportCoords[code];
            const wx = weatherByCode[code];
            const marker = L.marker([lat, lon], { title: code, icon: L.icon({
                iconUrl: 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon.png',
                iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] })
            }).addTo(map);
            marker.bindPopup(`<strong>Fuel Stop</strong><br>${code}<br>${wx.temperature !== undefined ? `Temp: ${wx.temperature}&deg;C<br>Wind: ${wx.windspeed} kt` : 'Weather unavailable'}`);
            fuelStopMarkers.push(marker);
        });
        // Mark start/end with weather popups
        const endpoints = [legs[0].from, legs[legs.length-1].to];
        endpoints.forEach(code => {
            const [lat, lon] = airportCoords[code];
            const wx = weatherByCode[code];
            const marker = L.marker([lat, lon], { title: code }).addTo(map);
            marker.bindPopup(`<strong>${code}</strong><br>${wx.temperature !== undefined ? `Temp: ${wx.temperature}&deg;C<br>Wind: ${wx.windspeed} kt` : 'Weather unavailable'}`);
            fuelStopMarkers.push(marker);
        });
        // Show summary with weather for each leg
        routeSummaryDiv.innerHTML = `<div class="route-stats">
            <b>Route:</b> ${from} → ${to}<br>
            <b>Total Distance:</b> ${data.total_distance_nm.toFixed(1)} nm<br>
            <b>Estimated Time:</b> ${data.estimated_time_hr.toFixed(2)} hr<br>
            <b>Fuel Stops:</b> ${data.fuel_stops.length > 0 ? data.fuel_stops.join(', ') : 'None'}<br>
        </div>
        <div class="route-legs"><b>Legs & Weather:</b><ul style='margin:0;padding-left:18px;'>
            ${legs.map((leg, i) => {
                const wx = weatherByCode[leg.from];
                return `<li>${leg.from} → ${leg.to}: ${leg.distance_nm.toFixed(1)} nm, FL${Math.round(leg.cruise_altitude_ft/100)} (${leg.cruise_altitude_ft} ft), ${leg.estimated_time_hr.toFixed(2)} hr` +
                    (wx.temperature !== undefined ? ` — <span style='color:#0077b6'>Temp: ${wx.temperature}&deg;C, Wind: ${wx.windspeed} kt</span>` : ' — Weather unavailable') +
                    `</li>`;
            }).join('')}
        </ul></div>`;
    } catch (error) {
        routeSummaryDiv.innerHTML = `<div class=\"error-message\">${error.message}</div>`;
    }
});

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
    
    // Check if airports overlay is enabled
    const airportsEnabled = overlayCheckboxes.airports.checked;
    
    // Fetch airports if the overlay is enabled
    if (airportsEnabled) {
        fetchAirports(lastKnownPosition.lat, lastKnownPosition.lng);
    }
});

// Function to get marker color based on flight category
function getFlightCategoryColor(category) {
    switch (category) {
        case 'VFR': return '#00ff00';  // Green
        case 'MVFR': return '#0000ff'; // Blue
        case 'IFR': return '#ff0000';  // Red
        case 'LIFR': return '#ff00ff'; // Magenta
        default: return '#808080';     // Grey
    }
}

// Function to create a dot icon
function createDotIcon(color) {
    return L.divIcon({
        className: 'airport-dot',
        html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });
}

function formatCeiling(ceiling_ft, ceiling_layer) {
    if (ceiling_ft === null || ceiling_layer === null) {
        return 'No ceiling';
    }
    return `${ceiling_layer} at ${ceiling_ft} ft`;
}

function formatVisibility(visibility_sm) {
    if (visibility_sm === null) {
        return 'Unknown visibility';
    }
    return `${visibility_sm} statute miles`;
}

function formatCloudLayers(layers) {
    if (!layers || layers.length === 0) {
        return 'Clear skies';
    }
    return layers.map(layer => `${layer.cover} at ${layer.base_ft} ft`).join('<br>');
}

// Function to fetch and display airports
async function fetchAirports(lat, lon) {
    try {
        const requestBody = {
            lat: lat,
            lon: lon,
            radius: 50  // 50km radius
        };
        
        const response = await fetch('/get_airports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Failed to fetch airports: ${errorData.details || errorData.error || response.statusText}`);
        }
        
        const data = await response.json();
        
        // Clear existing airport markers
        airportMarkers.forEach(marker => map.removeLayer(marker));
        airportMarkers = [];
        
        // Add new airport markers
        data.airports.forEach(airport => {
            // Get color based on flight category
            const color = getFlightCategoryColor(airport.weather?.flight_category);
            
            // Create tooltip text
            const tooltipText = `${airport.name} (${airport.weather?.flight_category || 'Unknown'})
${airport.weather?.ceiling_ft ? `Ceiling: ${formatCeiling(airport.weather?.ceiling_ft, airport.weather?.ceiling_layer)}` : airport.weather?.ceiling_layer === 'CLR' ? 'Ceiling: CLR' : 'No ceiling'}
${airport.weather?.wind_speed_kt ? `Winds: ${airport.weather.wind_speed_kt}kt at ${airport.weather.wind_dir_degrees}°` : 'Winds: N/A'}`;
            
            // Create marker with colored dot
            const marker = L.marker([airport.lat, airport.lon], {
                icon: createDotIcon(color)
            })
            .bindPopup(`
                <strong>${airport.name}</strong><br>
                ${airport.iata ? `IATA: ${airport.iata}<br>` : ''}
                ${airport.icao ? `ICAO: ${airport.icao}<br>` : ''}
                Type: ${airport.type}<br>
                Flight Category: ${airport.weather?.flight_category || 'Unknown'}<br>
                ${airport.weather?.ceiling_ft ? `Ceiling: ${formatCeiling(airport.weather?.ceiling_ft, airport.weather?.ceiling_layer)}` : airport.weather?.ceiling_layer === 'CLR' ? 'Ceiling: CLR' : 'No ceiling'}<br>
                Visibility: ${formatVisibility(airport.weather?.visibility_sm)}<br>
                Cloud Layers:<br>${formatCloudLayers(airport.weather?.all_layers)}
            `)
            .bindTooltip(tooltipText, {
                permanent: false,
                direction: 'top',
                offset: [0, -8],
                className: 'airport-tooltip'
            });
            
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
                fetchAirports(lastKnownPosition.lat, lastKnownPosition.lng);
            } else {
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
            <th>Cloud Cover</th>
            <th>Ceiling</th>
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

        // Format ceiling based on cloud cover and cloud base
        const cloudBase = data.daily.cloudbase_ft?.[index];
        const ceilingStr = formatCeiling(cloudCover, cloudBase);
        
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
            <td data-ceiling="${ceilingStr}">${ceilingStr}</td>
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

    // Basic validation for airport code format
    if (!/^[A-Z0-9]{3,4}$/.test(airportCode)) {
        const container = document.getElementById('forecast-container');
        container.innerHTML = `<div class="error-message">Invalid airport code format. Please enter a 3 or 4 character code (e.g., SFO or KSFO).</div>`;
        return;
    }

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
            throw new Error(errorData.details || errorData.error || `Airport "${airportCode}" not found. Please check the code and try again.`);
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

        // Clear any previous error messages
        const container = document.getElementById('forecast-container');
        if (container.querySelector('.error-message')) {
            container.innerHTML = '';
        }
    } catch (error) {
        const container = document.getElementById('forecast-container');
        const errorMessage = error.message.includes('400 Client Error') ? 
            `Airport "${airportCode}" not found. Please check the code and try again.` : 
            error.message;
        container.innerHTML = `<div class="error-message">${errorMessage}</div>`;
    }
}

// Function to format ceiling for forecast table
function formatCeiling(cloudCover, cloudBase) {
    if (cloudBase && cloudBase > 0) {
        return `${Math.round(cloudBase)} ft`;
    } else if (cloudCover < 30) {  // Show CLR when cloud cover is low
        return 'CLR';
    } else if (cloudCover >= 30 && !cloudBase) {  // Show OVC when cloudy but no base data
        return 'OVC';
    }
    return 'Unknown';
} 