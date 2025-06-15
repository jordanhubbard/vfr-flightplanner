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
    attribution: ' OpenStreetMap contributors'
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
let currentForecastDate = new Date(); // Track the current forecast date
const opacitySlider = document.getElementById('overlay-opacity');
const maxForecastDays = 16;  // Open-Meteo API limitation
const airportCodeInput = document.getElementById('airport-code');
const goAirportButton = document.getElementById('go-airport');

// Date navigation elements
const forecastDateInput = document.getElementById('forecast-date');
const prevDateButton = document.getElementById('prev-date');
const nextDateButton = document.getElementById('next-date');
const todayButton = document.getElementById('today-button');

// Initialize date picker with today's date
function initializeDatePicker() {
    const today = new Date();
    currentForecastDate = new Date(today);
    updateDateDisplay();
    updateNavigationButtons();
}

// Update the date input display
function updateDateDisplay() {
    const dateString = currentForecastDate.toISOString().split('T')[0];
    forecastDateInput.value = dateString;
}

// Update navigation button states
function updateNavigationButtons() {
    const today = new Date();
    const maxDate = new Date(today);
    maxDate.setDate(today.getDate() + maxForecastDays);
    
    // Disable previous button if we're at today
    prevDateButton.disabled = currentForecastDate.toDateString() === today.toDateString();
    
    // Disable next button if we're at max forecast date
    nextDateButton.disabled = currentForecastDate >= maxDate;
    
    // Update today button visibility
    todayButton.style.display = currentForecastDate.toDateString() === today.toDateString() ? 'none' : 'inline-block';
}

// Handle date changes
function handleDateChange(newDate) {
    currentForecastDate = new Date(newDate);
    updateDateDisplay();
    updateNavigationButtons();
    
    // Refresh weather data if we have a location
    if (lastKnownPosition) {
        fetchWeatherData();
    }
}

// Event listeners for date navigation
prevDateButton.addEventListener('click', () => {
    const newDate = new Date(currentForecastDate);
    newDate.setDate(newDate.getDate() - 1);
    handleDateChange(newDate);
});

nextDateButton.addEventListener('click', () => {
    const newDate = new Date(currentForecastDate);
    newDate.setDate(newDate.getDate() + 1);
    handleDateChange(newDate);
});

todayButton.addEventListener('click', () => {
    handleDateChange(new Date());
});

forecastDateInput.addEventListener('change', (e) => {
    const selectedDate = new Date(e.target.value);
    handleDateChange(selectedDate);
});

// Initialize date picker
initializeDatePicker();

// Function to get active overlays
function getActiveOverlays() {
    const overlays = [];
    if (overlayCheckboxes.clouds && overlayCheckboxes.clouds.checked) overlays.push('clouds');
    if (overlayCheckboxes.precipitation && overlayCheckboxes.precipitation.checked) overlays.push('precipitation');
    if (overlayCheckboxes.wind && overlayCheckboxes.wind.checked) overlays.push('wind');
    if (overlayCheckboxes.temp && overlayCheckboxes.temp.checked) overlays.push('temp');
    if (overlayCheckboxes.airports && overlayCheckboxes.airports.checked) overlays.push('airports');
    return overlays;
}

// Airport status elements
const airportStatusElements = {
    loading: document.getElementById('airport-loading'),
    ready: document.getElementById('airport-ready'),
    error: document.getElementById('airport-error'),
    count: document.getElementById('airport-count'),
    refreshBtn: document.getElementById('refresh-airports'),
    refreshErrorBtn: document.getElementById('refresh-airports-error')
};

// Airport status management
let airportStatusCheckInterval = null;
let isRefreshing = false;

// Initialize airport status checking
function initializeAirportStatus() {
    checkAirportStatus();
    
    // Check status every 30 seconds
    airportStatusCheckInterval = setInterval(checkAirportStatus, 30000);
    
    // Add event listeners for refresh buttons
    if (airportStatusElements.refreshBtn) {
        airportStatusElements.refreshBtn.addEventListener('click', refreshAirportData);
    }
    if (airportStatusElements.refreshErrorBtn) {
        airportStatusElements.refreshErrorBtn.addEventListener('click', refreshAirportData);
    }
}

// Check airport cache status
async function checkAirportStatus() {
    try {
        const response = await fetch('/api/airport-cache-status');
        const status = await response.json();
        
        updateAirportStatusUI(status);
        
    } catch (error) {
        console.error('Error checking airport status:', error);
        showAirportError();
    }
}

// Update airport status UI based on backend response
function updateAirportStatusUI(status) {
    // Hide all status elements first
    hideAllAirportStatus();
    
    if (status.overall_status === 'ready') {
        // Show ready status
        if (airportStatusElements.ready) {
            airportStatusElements.ready.style.display = 'flex';
        }
        if (airportStatusElements.count) {
            airportStatusElements.count.textContent = status.openaip_cache.airport_count || 0;
        }
    } else if (status.overall_status === 'missing') {
        // Show loading or error based on whether we're currently refreshing
        if (isRefreshing) {
            showAirportLoading();
        } else {
            showAirportError();
        }
    }
}

// Show loading state
function showAirportLoading() {
    hideAllAirportStatus();
    if (airportStatusElements.loading) {
        airportStatusElements.loading.style.display = 'flex';
    }
}

// Show error state
function showAirportError() {
    hideAllAirportStatus();
    if (airportStatusElements.error) {
        airportStatusElements.error.style.display = 'flex';
    }
}

// Hide all airport status elements
function hideAllAirportStatus() {
    if (airportStatusElements.loading) airportStatusElements.loading.style.display = 'none';
    if (airportStatusElements.ready) airportStatusElements.ready.style.display = 'none';
    if (airportStatusElements.error) airportStatusElements.error.style.display = 'none';
}

// Refresh airport data
async function refreshAirportData() {
    if (isRefreshing) return; // Prevent multiple simultaneous refreshes
    
    isRefreshing = true;
    showAirportLoading();
    
    // Add refreshing class to buttons
    if (airportStatusElements.refreshBtn) {
        airportStatusElements.refreshBtn.classList.add('refreshing');
        airportStatusElements.refreshBtn.disabled = true;
    }
    if (airportStatusElements.refreshErrorBtn) {
        airportStatusElements.refreshErrorBtn.classList.add('refreshing');
        airportStatusElements.refreshErrorBtn.disabled = true;
    }
    
    try {
        const response = await fetch('/api/refresh-airport-cache', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            console.log('Airport cache refresh started');
            
            // Poll for completion (check every 5 seconds for up to 2 minutes)
            let attempts = 0;
            const maxAttempts = 24; // 2 minutes / 5 seconds
            
            const pollCompletion = async () => {
                attempts++;
                
                try {
                    const statusResponse = await fetch('/api/airport-cache-status');
                    const status = await statusResponse.json();
                    
                    if (status.overall_status === 'ready') {
                        // Success!
                        updateAirportStatusUI(status);
                        isRefreshing = false;
                        enableRefreshButtons();
                        console.log('Airport cache refresh completed successfully');
                        return;
                    }
                    
                    if (attempts < maxAttempts) {
                        // Continue polling
                        setTimeout(pollCompletion, 5000);
                    } else {
                        // Timeout - show error
                        console.warn('Airport cache refresh timed out');
                        showAirportError();
                        isRefreshing = false;
                        enableRefreshButtons();
                    }
                    
                } catch (error) {
                    console.error('Error polling airport status:', error);
                    if (attempts < maxAttempts) {
                        setTimeout(pollCompletion, 5000);
                    } else {
                        showAirportError();
                        isRefreshing = false;
                        enableRefreshButtons();
                    }
                }
            };
            
            // Start polling after a short delay
            setTimeout(pollCompletion, 5000);
            
        } else {
            throw new Error('Failed to start airport cache refresh');
        }
        
    } catch (error) {
        console.error('Error refreshing airport data:', error);
        showAirportError();
        isRefreshing = false;
        enableRefreshButtons();
    }
}

// Enable refresh buttons and remove refreshing state
function enableRefreshButtons() {
    if (airportStatusElements.refreshBtn) {
        airportStatusElements.refreshBtn.classList.remove('refreshing');
        airportStatusElements.refreshBtn.disabled = false;
    }
    if (airportStatusElements.refreshErrorBtn) {
        airportStatusElements.refreshErrorBtn.classList.remove('refreshing');
        airportStatusElements.refreshErrorBtn.disabled = false;
    }
}

// Initialize airport status checking
initializeAirportStatus();

// Area forecast functionality
const areaForecastInput = document.getElementById('area-forecast-airport');
const areaForecastButton = document.getElementById('get-area-forecast');

if (areaForecastButton) {
    areaForecastButton.addEventListener('click', handleAreaForecast);
}
if (areaForecastInput) {
    areaForecastInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleAreaForecast();
        }
    });
}

async function handleAreaForecast() {
    const airportCode = areaForecastInput ? areaForecastInput.value.trim().toUpperCase() : '';
    if (!airportCode) return;
    
    try {
        const response = await fetch('/get_area_forecast', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                airport_code: airportCode,
                forecast_date: currentForecastDate.toISOString().split('T')[0]
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get area forecast');
        }
        
        const data = await response.json();
        
        // Display the area forecast results
        displayAreaForecast(data);
        
    } catch (error) {
        console.error('Error getting area forecast:', error);
        alert('Failed to get area forecast. Please check the airport code.');
    }
}

function displayAreaForecast(data) {
    // This function would display the area forecast data
    // Implementation depends on how you want to show the results
    console.log('Area forecast data:', data);
}

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
    
    // Hide flight legs table initially
    const flightLegsContainer = document.getElementById('flight-legs-container');
    flightLegsContainer.style.display = 'none';

    const from = fromAirportInput.value.trim().toUpperCase();
    const to = toAirportInput.value.trim().toUpperCase();
    const range = parseFloat(aircraftRangeInput.value);
    const groundspeed = parseFloat(groundspeedInput.value);
    
    // Get new advanced parameters
    const fuelCapacity = parseFloat(document.getElementById('fuel-capacity').value);
    const fuelBurnRate = parseFloat(document.getElementById('fuel-burn-rate').value);
    const avoidTerrain = document.getElementById('avoid-terrain').checked;
    const planFuelStops = document.getElementById('plan-fuel-stops').checked;
    const cruisingAltitude = parseInt(document.getElementById('cruising-altitude').value);
    
    if (!from || !to || isNaN(range) || isNaN(groundspeed) || isNaN(fuelCapacity) || isNaN(fuelBurnRate) || isNaN(cruisingAltitude)) {
        routeSummaryDiv.innerHTML = '<div class="error-message">All fields are required.</div>';
        return;
    }
    try {
        routeSummaryDiv.innerHTML = 'Planning route...';
        const response = await fetch('/api/plan_route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                from, 
                to, 
                range, 
                groundspeed,
                fuel_capacity: fuelCapacity,
                fuel_burn_rate: fuelBurnRate,
                avoid_terrain: avoidTerrain,
                plan_fuel_stops: planFuelStops,
                cruising_altitude: cruisingAltitude
            })
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
        // Show flight legs table
        flightLegsContainer.style.display = 'block';
        displayFlightLegsTable(data, fuelCapacity, fuelBurnRate);
        
        // Fetch weather data along the route
        const routeWeatherData = await fetchRouteWeatherData(legs, cruisingAltitude);
        console.log('Route weather data:', routeWeatherData);
        
        // Display route weather information in the flight legs table
        displayFlightLegsTable(data, fuelCapacity, fuelBurnRate, routeWeatherData);
    } catch (error) {
        routeSummaryDiv.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
});

// Function to display flight legs table with fuel information
function displayFlightLegsTable(routeData, fuelCapacity, fuelBurnRate, routeWeatherData = null) {
    const flightLegsTableBody = document.getElementById('flight-legs-tbody');
    flightLegsTableBody.innerHTML = '';
    
    let currentFuel = fuelCapacity;
    let legNumber = 1;
    
    routeData.legs.forEach((leg, index) => {
        // Calculate fuel consumption for this leg
        const fuelUsed = leg.estimated_time_hr * fuelBurnRate;
        currentFuel -= fuelUsed;
        
        // Check if this is a fuel stop (intermediate airport)
        const isFuelStop = routeData.fuel_stops && routeData.fuel_stops.includes(leg.to);
        
        // Get weather information for this leg
        let windInfo = 'N/A';
        let windElement = null;
        if (routeWeatherData) {
            const legWeather = routeWeatherData.find(w => w.airport === leg.from || w.airport === leg.to);
            if (legWeather && legWeather.weather && legWeather.weather.current) {
                const current = legWeather.weather.current;
                if (current.wind_speed_10m && current.wind_direction_10m) {
                    const windSpeed = Math.round(current.wind_speed_10m * 1.94384); // Convert m/s to knots
                    const windDir = Math.round(current.wind_direction_10m);
                    windElement = getWindDisplayWithBarb(windSpeed, windDir);
                    windInfo = `${windDir.toString().padStart(3, '0')}°/${windSpeed}kt`;
                }
            }
        }
        
        // Fallback to placeholder if no real weather data
        if (windInfo === 'N/A') {
            windInfo = getWindDisplay(leg.cruise_altitude_ft || 6500);
        }
        
        // Create flight leg row
        const legRow = document.createElement('tr');
        legRow.className = 'flight-leg';
        legRow.innerHTML = `
            <td>Leg ${legNumber}</td>
            <td>${leg.from}</td>
            <td>${leg.to}</td>
            <td>${leg.distance_nm.toFixed(1)} nm</td>
            <td>${leg.cruise_altitude_ft || 6500} ft</td>
            <td>${(leg.estimated_time_hr * 60).toFixed(0)} min</td>
            <td class="wind-cell"></td>
            <td>${fuelUsed.toFixed(1)} gal</td>
            <td>${currentFuel.toFixed(1)} gal</td>
            <td>Flight</td>
        `;
        flightLegsTableBody.appendChild(legRow);
        
        // Add wind information to the wind cell
        const windCell = legRow.querySelector('.wind-cell');
        if (windElement) {
            windCell.appendChild(windElement);
        } else {
            windCell.textContent = windInfo;
        }
        
        // Add fuel stop row if this destination is a fuel stop
        if (isFuelStop) {
            const fuelStopRow = document.createElement('tr');
            fuelStopRow.className = 'fuel-stop';
            fuelStopRow.innerHTML = `
                <td>Stop ${legNumber}</td>
                <td colspan="2">${leg.to} - FUEL STOP</td>
                <td>-</td>
                <td>-</td>
                <td>30 min</td>
                <td>-</td>
                <td>0.0 gal</td>
                <td>${fuelCapacity.toFixed(1)} gal</td>
                <td>Refuel</td>
            `;
            flightLegsTableBody.appendChild(fuelStopRow);
            
            // Reset fuel to full capacity after fuel stop
            currentFuel = fuelCapacity;
        }
        
        legNumber++;
    });
    
    // Add summary row
    const summaryRow = document.createElement('tr');
    summaryRow.style.fontWeight = 'bold';
    summaryRow.style.borderTop = '2px solid #333';
    summaryRow.innerHTML = `
        <td colspan="4">TOTAL</td>
        <td>-</td>
        <td>${(routeData.estimated_time_hr * 60).toFixed(0)} min</td>
        <td>-</td>
        <td>${(routeData.estimated_time_hr * fuelBurnRate).toFixed(1)} gal</td>
        <td>-</td>
        <td>Summary</td>
    `;
    flightLegsTableBody.appendChild(summaryRow);
}

// Function to get wind display (placeholder for wind barb visualization)
function getWindDisplay(altitude) {
    // This is a placeholder - in a real implementation, this would fetch actual wind data
    // For now, return a simulated wind display
    const windSpeed = Math.floor(Math.random() * 30) + 5; // 5-35 knots
    const windDirection = Math.floor(Math.random() * 360); // 0-359 degrees
    
    return `${windDirection.toString().padStart(3, '0')}°/${windSpeed}kt`;
}

// Function to create wind barb SVG element
function createWindBarb(windSpeed, windDirection, size = 30) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
    svg.style.display = 'inline-block';
    svg.style.verticalAlign = 'middle';
    
    const centerX = size / 2;
    const centerY = size / 2;
    const lineLength = size * 0.4;
    
    // Convert wind direction to radians (wind direction is where wind is coming FROM)
    const angleRad = (windDirection - 90) * Math.PI / 180;
    
    // Main wind direction line
    const endX = centerX + Math.cos(angleRad) * lineLength;
    const endY = centerY + Math.sin(angleRad) * lineLength;
    
    const mainLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    mainLine.setAttribute('x1', centerX);
    mainLine.setAttribute('y1', centerY);
    mainLine.setAttribute('x2', endX);
    mainLine.setAttribute('y2', endY);
    mainLine.setAttribute('stroke', '#333');
    mainLine.setAttribute('stroke-width', '2');
    svg.appendChild(mainLine);
    
    // Add wind speed barbs
    let remainingSpeed = Math.round(windSpeed);
    let barbPosition = 0.8; // Start near the end of the line
    
    // 50-knot pennants (triangular flags)
    while (remainingSpeed >= 50) {
        const barbX = centerX + Math.cos(angleRad) * lineLength * barbPosition;
        const barbY = centerY + Math.sin(angleRad) * lineLength * barbPosition;
        
        const perpAngle = angleRad + Math.PI / 2;
        const flagLength = size * 0.15;
        
        const flag = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        const points = [
            `${barbX},${barbY}`,
            `${barbX + Math.cos(perpAngle) * flagLength},${barbY + Math.sin(perpAngle) * flagLength}`,
            `${barbX + Math.cos(angleRad) * flagLength * 0.5},${barbY + Math.sin(angleRad) * flagLength * 0.5}`
        ].join(' ');
        flag.setAttribute('points', points);
        flag.setAttribute('fill', '#333');
        svg.appendChild(flag);
        
        remainingSpeed -= 50;
        barbPosition -= 0.15;
    }
    
    // 10-knot barbs (full lines)
    while (remainingSpeed >= 10) {
        const barbX = centerX + Math.cos(angleRad) * lineLength * barbPosition;
        const barbY = centerY + Math.sin(angleRad) * lineLength * barbPosition;
        
        const perpAngle = angleRad + Math.PI / 2;
        const barbLength = size * 0.12;
        
        const barb = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        barb.setAttribute('x1', barbX);
        barb.setAttribute('y1', barbY);
        barb.setAttribute('x2', barbX + Math.cos(perpAngle) * barbLength);
        barb.setAttribute('y2', barbY + Math.sin(perpAngle) * barbLength);
        barb.setAttribute('stroke', '#333');
        barb.setAttribute('stroke-width', '2');
        svg.appendChild(barb);
        
        remainingSpeed -= 10;
        barbPosition -= 0.1;
    }
    
    // 5-knot barbs (half lines)
    if (remainingSpeed >= 5) {
        const barbX = centerX + Math.cos(angleRad) * lineLength * barbPosition;
        const barbY = centerY + Math.sin(angleRad) * lineLength * barbPosition;
        
        const perpAngle = angleRad + Math.PI / 2;
        const barbLength = size * 0.06;
        
        const halfBarb = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        halfBarb.setAttribute('x1', barbX);
        halfBarb.setAttribute('y1', barbY);
        halfBarb.setAttribute('x2', barbX + Math.cos(perpAngle) * barbLength);
        halfBarb.setAttribute('y2', barbY + Math.sin(perpAngle) * barbLength);
        halfBarb.setAttribute('stroke', '#333');
        halfBarb.setAttribute('stroke-width', '2');
        svg.appendChild(halfBarb);
    }
    
    // Add calm indicator for very light winds
    if (windSpeed < 3) {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', centerX);
        circle.setAttribute('cy', centerY);
        circle.setAttribute('r', size * 0.1);
        circle.setAttribute('fill', 'none');
        circle.setAttribute('stroke', '#333');
        circle.setAttribute('stroke-width', '2');
        svg.appendChild(circle);
    }
    
    return svg;
}

// Enhanced wind display function with barb visualization
function getWindDisplayWithBarb(windSpeed, windDirection, altitude = null) {
    const windText = `${windDirection.toString().padStart(3, '0')}°/${windSpeed}kt`;
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.gap = '5px';
    
    // Add wind barb
    const windBarb = createWindBarb(windSpeed, windDirection, 25);
    container.appendChild(windBarb);
    
    // Add text
    const textSpan = document.createElement('span');
    textSpan.textContent = windText;
    textSpan.style.fontSize = '12px';
    container.appendChild(textSpan);
    
    return container;
}

// Add area forecast functionality
document.getElementById('area-forecast-btn').addEventListener('click', async function() {
    const airportCode = document.getElementById('area-forecast-airport').value.trim().toUpperCase();
    if (!airportCode) {
        alert('Please enter an airport code');
        return;
    }
    
    try {
        // Get airport coordinates
        const airportResponse = await fetch(`/api/airport?code=${airportCode}`);
        const airportData = await airportResponse.json();
        
        if (!airportResponse.ok) {
            alert(`Airport ${airportCode} not found`);
            return;
        }
        
        // Center map on airport and show 50nm radius
        const lat = airportData.latitude;
        const lon = airportData.longitude;
        map.setView([lat, lon], 9);
        
        // Add a circle to show 50nm radius
        if (window.areaForecastCircle) {
            map.removeLayer(window.areaForecastCircle);
        }
        
        // Convert 50nm to meters (1 nautical mile = 1852 meters)
        const radiusMeters = 50 * 1852;
        window.areaForecastCircle = L.circle([lat, lon], {
            radius: radiusMeters,
            color: '#ff7800',
            weight: 2,
            fillColor: '#ff7800',
            fillOpacity: 0.1
        }).addTo(map);
        
        // Set the position for weather data fetching
        lastKnownPosition = { lat: lat, lng: lon };
        
        // Fetch weather data for the area
        await fetchWeatherData(lat, lon);
        updateSelectedLocation(lat, lon);
        
    } catch (error) {
        console.error('Error fetching area forecast:', error);
        alert('Error fetching area forecast');
    }
});

// Weather overlay layers
let weatherLayers = {
    clouds: L.tileLayer(`https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: ' OpenWeatherMap',
        opacity: 0.7
    }),
    precipitation: L.tileLayer(`https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: ' OpenWeatherMap',
        opacity: 0.7
    }),
    wind: L.tileLayer(`https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: ' OpenWeatherMap',
        opacity: 0.7
    }),
    temp: L.tileLayer(`https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {
        attribution: ' OpenWeatherMap',
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

// Airport search functionality
goAirportButton.addEventListener('click', handleAirportSearch);
airportCodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleAirportSearch();
    }
});

async function handleAirportSearch() {
    const airportCode = airportCodeInput.value.trim().toUpperCase();
    if (!airportCode) return;
    
    try {
        const response = await fetch('/get_airport_coordinates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ airport_code: airportCode })
        });
        
        if (!response.ok) {
            throw new Error('Airport not found');
        }
        
        const data = await response.json();
        const lat = data.latitude;
        const lon = data.longitude;
        
        // Update map view and fetch weather
        map.setView([lat, lon], 10);
        updateSelectedLocation(lat, lon);
        await fetchWeatherData(lat, lon);
        
    } catch (error) {
        console.error('Error searching for airport:', error);
        alert('Airport not found. Please check the airport code.');
    }
}

// Handle map clicks
map.on('click', async function(e) {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;
    
    // Update location display and marker
    updateSelectedLocation(lat, lon);
    
    // Fetch weather data for the clicked location
    await fetchWeatherData(lat, lon);
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

Object.entries(overlayCheckboxes).forEach(([type, checkbox]) => {
    if (checkbox) {
        checkbox.addEventListener('change', function(e) {
            if (type === 'airports') {
                // Handle airports overlay specially
                if (e.target.checked && lastKnownPosition) {
                    fetchAirports(lastKnownPosition.lat, lastKnownPosition.lng);
                } else if (!e.target.checked) {
                    // Clear airport markers when disabled
                    airportMarkers.forEach(marker => map.removeLayer(marker));
                    airportMarkers = [];
                }
            } else {
                // Handle weather overlays
                toggleOverlay(type, e.target.checked);
                
                // Refresh weather data if we have a location
                if (lastKnownPosition) {
                    fetchWeatherData();
                }
            }
        });
    }
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
async function fetchWeatherData(lat = null, lon = null) {
    // Use provided parameters or fall back to current position
    const targetLat = lat || (lastKnownPosition ? lastKnownPosition.lat : null);
    const targetLon = lon || (lastKnownPosition ? lastKnownPosition.lng : null);
    
    if (!targetLat || !targetLon) {
        console.warn('No coordinates available for weather fetch');
        return null;
    }
    
    try {
        const response = await fetch('/get_weather', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lat: targetLat,
                lon: targetLon,
                forecast_date: currentForecastDate.toISOString().split('T')[0],  // Send date in YYYY-MM-DD format
                overlays: getActiveOverlays()
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Only update the display if this is for the current position
        if (!lat && !lon) {
            displayWeatherData(data);
        }
        
        return data;
    } catch (error) {
        console.error('Error fetching weather data:', error);
        
        // Only show error in UI if this is for the current position
        if (!lat && !lon) {
            const weatherContainer = document.getElementById('weather-info');
            if (weatherContainer) {
                weatherContainer.innerHTML = '<div class="error-message">Failed to load weather data. Please try again.</div>';
            }
        }
        
        return null;
    }
}

// Display weather data in the weather information container
function displayWeatherData(data) {
    const container = document.getElementById('weather-info');
    if (!container) return;

    let html = '<div class="weather-header"><h2>Weather Information</h2></div>';
    
    if (data.current) {
        const current = data.current;
        html += '<div class="current-weather">';
        html += '<h3>Current Conditions</h3>';
        html += '<div class="weather-details">';
        html += `<div class="weather-detail"><strong>Temperature:</strong> ${Math.round(current.temperature_2m)}°C</div>`;
        html += `<div class="weather-detail"><strong>Humidity:</strong> ${Math.round(current.relative_humidity_2m)}%</div>`;
        html += `<div class="weather-detail"><strong>Pressure:</strong> ${Math.round(current.surface_pressure)} hPa</div>`;
        html += `<div class="weather-detail"><strong>Cloud Cover:</strong> ${Math.round(current.cloud_cover)}%</div>`;
        
        // Add wind information with barb
        if (current.wind_speed_10m && current.wind_direction_10m) {
            const windSpeed = Math.round(current.wind_speed_10m * 1.94384); // Convert m/s to knots
            const windDir = Math.round(current.wind_direction_10m);
            html += `<div class="weather-detail wind-detail"><strong>Wind:</strong> <span id="current-wind-display"></span></div>`;
        }
        
        html += '</div></div>';
    }

    if (data.hourly && data.hourly.time) {
        html += '<div class="hourly-forecast">';
        html += '<h3>Hourly Forecast</h3>';
        html += '<div class="forecast-grid">';
        
        const maxHours = Math.min(24, data.hourly.time.length);
        for (let i = 0; i < maxHours; i += 3) { // Show every 3 hours
            const time = new Date(data.hourly.time[i]);
            const temp = Math.round(data.hourly.temperature_2m[i]);
            const windSpeed = data.hourly.wind_speed_10m ? Math.round(data.hourly.wind_speed_10m[i] * 1.94384) : 0;
            const windDir = data.hourly.wind_direction_10m ? Math.round(data.hourly.wind_direction_10m[i]) : 0;
            
            html += '<div class="forecast-item">';
            html += `<div class="forecast-time">${time.getHours().toString().padStart(2, '0')}:00</div>`;
            html += `<div class="forecast-temp">${temp}°C</div>`;
            html += `<div class="forecast-wind" id="wind-${i}"></div>`;
            html += '</div>';
        }
        
        html += '</div></div>';
    }

    container.innerHTML = html;
    
    // Add wind barbs to current conditions
    if (data.current && data.current.wind_speed_10m && data.current.wind_direction_10m) {
        const windSpeed = Math.round(data.current.wind_speed_10m * 1.94384);
        const windDir = Math.round(data.current.wind_direction_10m);
        const currentWindDisplay = document.getElementById('current-wind-display');
        if (currentWindDisplay) {
            const windElement = getWindDisplayWithBarb(windSpeed, windDir);
            currentWindDisplay.appendChild(windElement);
        }
    }
    
    // Add wind barbs to hourly forecast
    if (data.hourly && data.hourly.time) {
        const maxHours = Math.min(24, data.hourly.time.length);
        for (let i = 0; i < maxHours; i += 3) {
            const windSpeed = data.hourly.wind_speed_10m ? Math.round(data.hourly.wind_speed_10m[i] * 1.94384) : 0;
            const windDir = data.hourly.wind_direction_10m ? Math.round(data.hourly.wind_direction_10m[i]) : 0;
            
            const windElement = document.getElementById(`wind-${i}`);
            if (windElement && windSpeed > 0) {
                const windBarb = getWindDisplayWithBarb(windSpeed, windDir);
                windElement.appendChild(windBarb);
            }
        }
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

// Function to update selected location display
function updateSelectedLocation(lat, lon) {
    const locationText = document.getElementById('selected-location');
    if (locationText) {
        locationText.textContent = `Selected Location: ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°W`;
    }
    
    // Update global position for backward compatibility
    lastKnownPosition = { lat: lat, lng: lon };
    
    // Update marker position
    if (currentMarker) {
        currentMarker.setLatLng([lat, lon]);
    } else {
        currentMarker = L.marker([lat, lon]).addTo(map);
    }
    
    // Fetch airports if overlay is enabled
    const airportsCheckbox = document.getElementById('airports-overlay');
    if (airportsCheckbox && airportsCheckbox.checked) {
        fetchAirports(lat, lon);
    }
}

// Function to fetch weather data along a flight route
async function fetchRouteWeatherData(routeLegs, cruisingAltitude = 6500) {
    const weatherData = [];
    
    for (const leg of routeLegs) {
        try {
            // Fetch weather for departure airport
            const depResponse = await fetch(`/api/airport?code=${leg.from}`);
            const depAirport = await depResponse.json();
            
            if (depResponse.ok) {
                const depWeather = await fetchWeatherData(depAirport.latitude, depAirport.longitude, 1);
                if (depWeather) {
                    weatherData.push({
                        airport: leg.from,
                        name: depAirport.name,
                        lat: depAirport.latitude,
                        lon: depAirport.longitude,
                        weather: depWeather,
                        type: 'departure'
                    });
                }
            }
            
            // Fetch weather for arrival airport
            const arrResponse = await fetch(`/api/airport?code=${leg.to}`);
            const arrAirport = await arrResponse.json();
            
            if (arrResponse.ok) {
                const arrWeather = await fetchWeatherData(arrAirport.latitude, arrAirport.longitude, 1);
                if (arrWeather) {
                    weatherData.push({
                        airport: leg.to,
                        name: arrAirport.name,
                        lat: arrAirport.latitude,
                        lon: arrAirport.longitude,
                        weather: arrWeather,
                        type: 'arrival'
                    });
                }
            }
            
            // Fetch weather at 20nm intervals along the leg (for future enhancement)
            const numIntervals = Math.max(1, Math.floor(leg.distance_nm / 20));
            for (let i = 1; i < numIntervals; i++) {
                const fraction = i / numIntervals;
                const intermediateLat = depAirport.latitude + (arrAirport.latitude - depAirport.latitude) * fraction;
                const intermediateLon = depAirport.longitude + (arrAirport.longitude - depAirport.longitude) * fraction;
                
                const intermediateWeather = await fetchWeatherData(intermediateLat, intermediateLon, 1);
                if (intermediateWeather) {
                    weatherData.push({
                        airport: `${leg.from}-${leg.to}-${i}`,
                        name: `Waypoint ${i}`,
                        lat: intermediateLat,
                        lon: intermediateLon,
                        weather: intermediateWeather,
                        type: 'waypoint',
                        distance_from_departure: leg.distance_nm * fraction
                    });
                }
            }
            
        } catch (error) {
            console.error(`Error fetching weather for leg ${leg.from} to ${leg.to}:`, error);
        }
    }
    
    return weatherData;
}