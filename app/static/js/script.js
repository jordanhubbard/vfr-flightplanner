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

// Loading and Toast Notification System
class LoadingManager {
    static showLoading(element, message = 'Loading...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.classList.add('loading');
            if (message && element.dataset) {
                element.dataset.loadingMessage = message;
            }
        }
    }

    static hideLoading(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.classList.remove('loading');
            if (element.dataset) {
                delete element.dataset.loadingMessage;
            }
        }
    }

    static showButtonLoading(button, originalText) {
        if (typeof button === 'string') {
            button = document.getElementById(button);
        }
        if (button) {
            button.classList.add('btn-loading');
            button.disabled = true;
            if (originalText) {
                button.dataset.originalText = originalText;
                const textSpan = button.querySelector('.btn-text') || button;
                textSpan.textContent = 'Loading...';
            }
        }
    }

    static hideButtonLoading(button) {
        if (typeof button === 'string') {
            button = document.getElementById(button);
        }
        if (button) {
            button.classList.remove('btn-loading');
            button.disabled = false;
            if (button.dataset.originalText) {
                const textSpan = button.querySelector('.btn-text') || button;
                textSpan.textContent = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        }
    }
}

class ToastManager {
    static container = null;

    static init() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.id = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    static show(message, type = 'info', duration = 5000) {
        if (!this.container) this.init();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const header = document.createElement('div');
        header.className = 'toast-header';
        
        const body = document.createElement('div');
        body.className = 'toast-body';
        body.textContent = message;

        // Set header based on type
        switch (type) {
            case 'success':
                header.textContent = '✓ Success';
                break;
            case 'error':
                header.textContent = '✗ Error';
                break;
            case 'warning':
                header.textContent = '⚠ Warning';
                break;
            case 'info':
            default:
                header.textContent = 'ℹ Information';
                break;
        }

        toast.appendChild(header);
        toast.appendChild(body);
        this.container.appendChild(toast);

        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Auto-hide toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);

        return toast;
    }

    static success(message, duration = 4000) {
        return this.show(message, 'success', duration);
    }

    static error(message, duration = 6000) {
        return this.show(message, 'error', duration);
    }

    static warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    }

    static info(message, duration = 4000) {
        return this.show(message, 'info', duration);
    }
}

// Initialize toast system
ToastManager.init();

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
            // Extract services from response
            const services = data.services || {};
            const owm = services.openweathermap || {};
            const meteo = services.openmeteo || {};
            
            // Update OpenWeatherMap status
            owmStatus.className = `status-dot ${owm.status ? 'online' : 'offline'}`;
            if (!owm.status) {
                owmErrorMessage.textContent = owm.error || 'Unknown error';
                owmIndicator.classList.add('show-error');
            } else {
                owmErrorMessage.textContent = 'No errors reported';
                owmIndicator.classList.remove('show-error');
            }
            owmLastCheck.textContent = `Last checked: ${formatTimestamp(owm.timestamp)}`;
            owmCalls.textContent = `API calls: ${owm.api_calls || 0}`;
            
            // Update Open-Meteo status
            meteoStatus.className = `status-dot ${meteo.status ? 'online' : 'offline'}`;
            if (!meteo.status) {
                meteoErrorMessage.textContent = meteo.error || 'Unknown error';
                meteoIndicator.classList.add('show-error');
            } else {
                meteoErrorMessage.textContent = 'No errors reported';
                meteoIndicator.classList.remove('show-error');
            }
            meteoLastCheck.textContent = `Last checked: ${formatTimestamp(meteo.timestamp)}`;
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
let windBarbMarkers = [];  // Array to store wind barb markers
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
            airportStatusElements.count.textContent = status.airport_cache.airport_count || 0;
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
    const flightPlannerSection = document.querySelector('.flight-planner-controls');
    const submitButton = flightPlanForm.querySelector('button[type="submit"]');
    
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
        ToastManager.error('All fields are required.');
        return;
    }
    
    // Show loading state
    LoadingManager.showButtonLoading(submitButton, 'Plan Flight');
    flightPlannerSection.classList.add('loading');
    ToastManager.info(`Planning flight route from ${from} to ${to}...`);
    
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
            ToastManager.error(data.error || 'Failed to plan route.');
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
            const wres = await fetch('/get_weather', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    lat, 
                    lon, 
                    forecast_date: new Date().toISOString().split('T')[0],
                    overlays: []
                })
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
        
        // Fetch comprehensive route weather summary
        const routeWeatherSummary = await fetchRouteWeatherSummary(routeCoords, cruisingAltitude);
        console.log('Route weather summary:', routeWeatherSummary);
        
        // Display route weather information in the flight legs table
        displayFlightLegsTable(data, fuelCapacity, fuelBurnRate, routeWeatherSummary);
        
        // Display overall route weather summary
        if (routeWeatherSummary && routeWeatherSummary.summary) {
            displayRouteWeatherSummary(routeWeatherSummary.summary);
        }
        
        // Add weather markers along the route
        if (routeWeatherSummary && routeWeatherSummary.waypoint_weather) {
            addRouteWeatherMarkers(routeWeatherSummary.waypoint_weather);
        }
        
        // Make the route polyline clickable for detailed weather
        makeRouteClickable(routePolyline, cruisingAltitude);
        
        ToastManager.success(`Flight route planned successfully from ${from} to ${to}`);
    } catch (error) {
        routeSummaryDiv.innerHTML = `<div class="error-message">${error.message}</div>`;
        ToastManager.error('Flight planning failed: ' + error.message);
    } finally {
        // Hide loading state
        LoadingManager.hideButtonLoading(submitButton);
        flightPlannerSection.classList.remove('loading');
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
    if (!airportCode) {
        ToastManager.warning('Please enter an airport code');
        return;
    }
    
    // Show loading state
    LoadingManager.showButtonLoading(goAirportButton, 'Go');
    ToastManager.info(`Searching for airport ${airportCode}...`);
    
    try {
        const response = await fetch(`/api/airport?code=${airportCode}`);
        
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
        
        ToastManager.success(`Found airport ${airportCode}: ${data.name || 'Unknown Name'}`);
        
        // Clear the input
        airportCodeInput.value = '';
        
    } catch (error) {
        console.error('Error searching for airport:', error);
        ToastManager.error('Airport not found. Please check the airport code.');
    } finally {
        // Hide loading state
        LoadingManager.hideButtonLoading(goAirportButton);
    }
}

// Handle map clicks
map.on('click', async function(e) {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;
    
    // Update location display and marker
    updateSelectedLocation(lat, lon);
    
    // Fetch weather data for the clicked location (fetchWeatherData already has loading feedback)
    await fetchWeatherData(lat, lon);
});

// Handle map view changes (pan/zoom) to update wind barbs
map.on('moveend', function(e) {
    // Only update wind barbs if wind overlay is enabled and we have a position
    const windCheckbox = document.getElementById('wind-overlay');
    if (windCheckbox && windCheckbox.checked && lastKnownPosition) {
        fetchWindBarbs(lastKnownPosition.lat, lastKnownPosition.lng);
    }
});

// Function to get marker color based on flight category
function getFlightCategoryColor(category) {
    switch (category) {
        case 'VFR': return '#00C851';   // Aviation Green
        case 'MVFR': return '#007CBA';  // Aviation Blue  
        case 'IFR': return '#CC0000';   // Aviation Red
        case 'LIFR': return '#AA00FF';  // Aviation Magenta/Purple
        default: return '#6C757D';      // Gray for unknown
    }
}

// Function to create a dot icon with aviation sectional chart styling
function createDotIcon(color, category = 'Unknown') {
    return L.divIcon({
        className: 'airport-weather-dot',
        html: `<div class="weather-dot" style="background-color: ${color};" title="${category}"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
    });
}

// Function to create a wind barb icon for the map
function createWindBarbIcon(windSpeed, windDirection) {
    const windBarb = createWindBarb(windSpeed, windDirection, 40);
    windBarb.style.filter = 'drop-shadow(1px 1px 2px rgba(0,0,0,0.5))';
    
    return L.divIcon({
        className: 'wind-barb-marker',
        html: windBarb.outerHTML,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
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
    // Show loading feedback
    LoadingManager.showLoading('map', 'Loading nearby airports...');
    ToastManager.info('Loading nearby airports...');
    
    try {
        const requestBody = {
            lat: lat,
            lon: lon,
            radius: 50  // 50km radius
        };
        
        const response = await fetch(`/api/airports`, {
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
            // Get flight category and color
            const flightCategory = airport.weather?.flight_category || 'Unknown';
            const color = getFlightCategoryColor(flightCategory);
            
            // Create tooltip text
            const tooltipText = `${airport.name} (${flightCategory})
${airport.weather?.ceiling_ft ? `Ceiling: ${formatCeiling(airport.weather?.ceiling_ft, airport.weather?.ceiling_layer)}` : airport.weather?.ceiling_layer === 'CLR' ? 'Ceiling: CLR' : 'No ceiling'}
${airport.weather?.wind_speed_kt ? `Winds: ${airport.weather.wind_speed_kt}kt at ${airport.weather.wind_dir_degrees}°` : 'Winds: N/A'}`;
            
            if (airport.latitude && airport.longitude) {
                // Create marker with colored dot
                const marker = L.marker([airport.latitude, airport.longitude], {
                    icon: createDotIcon(color, flightCategory)
                })
                .bindPopup(`
                    <div style="text-align: center; margin-bottom: 8px;">
                        <strong>${airport.name}</strong><br>
                        ${airport.iata ? `${airport.iata}` : ''}${airport.icao ? `${airport.iata ? ' / ' : ''}${airport.icao}` : ''}
                    </div>
                    <div style="text-align: center; margin-bottom: 8px;">
                        <span style="background-color: ${color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">
                            ${flightCategory}
                        </span>
                    </div>
                    <div style="font-size: 12px;">
                        <strong>Type:</strong> ${airport.type}<br>
                        <strong>Ceiling:</strong> ${airport.weather?.ceiling_ft ? formatCeiling(airport.weather?.ceiling_ft, airport.weather?.ceiling_layer) : airport.weather?.ceiling_layer === 'CLR' ? 'CLR' : 'No ceiling'}<br>
                        <strong>Visibility:</strong> ${formatVisibility(airport.weather?.visibility_sm)}<br>
                        <strong>Winds:</strong> ${airport.weather?.wind_speed_kt ? `${airport.weather.wind_speed_kt}kt @ ${airport.weather.wind_dir_degrees}°` : 'N/A'}<br>
                        <strong>Clouds:</strong><br>${formatCloudLayers(airport.weather?.all_layers)}
                    </div>
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
            } else {
                console.warn('Skipping airport with invalid coordinates:', airport);
            }
        });
        
        ToastManager.success(`Loaded ${data.count} nearby airports`);
        
        // Show weather legend if airports are displayed
        if (overlayCheckboxes.airports.checked) {
            document.getElementById('weather-legend').style.display = 'block';
        }
    } catch (error) {
        console.error('Error fetching airports:', error);
        ToastManager.error('Failed to load nearby airports: ' + error.message);
    } finally {
        // Hide loading state
        LoadingManager.hideLoading('map');
    }
}

// Function to fetch and display wind barbs on the map
async function fetchWindBarbs(lat, lon) {
    // Show loading feedback
    LoadingManager.showLoading('map', 'Loading wind data...');
    ToastManager.info('Loading wind barbs...');
    
    try {
        // Create a grid of points around the current location
        const bounds = map.getBounds();
        const latStep = (bounds.getNorth() - bounds.getSouth()) / 6; // 6x6 grid
        const lonStep = (bounds.getEast() - bounds.getWest()) / 6;
        
        // Clear existing wind barb markers
        windBarbMarkers.forEach(marker => map.removeLayer(marker));
        windBarbMarkers = [];
        
        const windPromises = [];
        
        // Create grid points
        for (let i = 1; i < 6; i++) {
            for (let j = 1; j < 6; j++) {
                const gridLat = bounds.getSouth() + (latStep * i);
                const gridLon = bounds.getWest() + (lonStep * j);
                
                windPromises.push(
                    fetch('/api/weather', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            lat: gridLat,
                            lon: gridLon,
                            days: 1,
                            overlays: []
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Extract current conditions from first forecast item
                        const current = data.forecast && data.forecast[0];
                        if (!current) {
                            return null;
                        }
                        // Convert wind speed from m/s to knots
                        const windSpeedKt = Math.round((current.wind_speed || 0) * 1.94384);
                        return {
                            lat: gridLat,
                            lon: gridLon,
                            windSpeed: windSpeedKt,
                            windDirection: current.wind_direction || 0
                        };
                    })
                    .catch(error => {
                        console.error('Error fetching wind data:', error);
                        return null;
                    })
                );
            }
        }
        
        const windData = await Promise.all(windPromises);
        
        // Add wind barb markers for valid data
        windData.forEach(point => {
            if (point && point.windSpeed > 0) {
                const marker = L.marker([point.lat, point.lon], {
                    icon: createWindBarbIcon(point.windSpeed, point.windDirection)
                })
                .bindTooltip(`Wind: ${point.windDirection}° @ ${point.windSpeed}kt`, {
                    permanent: false,
                    direction: 'top',
                    offset: [0, -20],
                    className: 'wind-tooltip'
                });
                
                // Only add to map if wind overlay is checked
                if (overlayCheckboxes.wind.checked) {
                    marker.addTo(map);
                }
                
                windBarbMarkers.push(marker);
            }
        });
        
        ToastManager.success(`Loaded ${windBarbMarkers.length} wind barbs`);
        
    } catch (error) {
        console.error('Error fetching wind data:', error);
        ToastManager.error('Failed to load wind data: ' + error.message);
    } finally {
        // Hide loading state
        LoadingManager.hideLoading('map');
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
                    // Show weather legend
                    document.getElementById('weather-legend').style.display = 'block';
                } else if (!e.target.checked) {
                    // Clear airport markers when disabled
                    airportMarkers.forEach(marker => map.removeLayer(marker));
                    airportMarkers = [];
                    // Hide weather legend
                    document.getElementById('weather-legend').style.display = 'none';
                }
            } else if (type === 'wind') {
                // Handle wind overlay specially for barbs
                toggleOverlay(type, e.target.checked);
                
                if (e.target.checked && lastKnownPosition) {
                    // Show wind barbs when wind overlay is enabled
                    fetchWindBarbs(lastKnownPosition.lat, lastKnownPosition.lng);
                } else if (!e.target.checked) {
                    // Hide wind barbs when disabled
                    windBarbMarkers.forEach(marker => map.removeLayer(marker));
                }
                
                // Also refresh weather data if we have a location
                if (lastKnownPosition) {
                    fetchWeatherData();
                }
            } else {
                // Handle other weather overlays
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
const opacityValue = document.getElementById('opacity-value');
opacitySlider.addEventListener('input', (e) => {
    const opacity = e.target.value / 100;
    const percentage = e.target.value;
    
    // Update the displayed value
    if (opacityValue) {
        opacityValue.textContent = percentage + '%';
    }
    
    // Update all active weather layers
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
    
    // Show loading state for main weather display
    const isMainWeatherRequest = !lat && !lon;
    if (isMainWeatherRequest) {
        LoadingManager.showLoading('weather-info', 'Loading weather data...');
        ToastManager.info('Fetching weather data...');
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
        if (isMainWeatherRequest) {
            LoadingManager.hideLoading('weather-info');
            displayWeatherData(data);
            ToastManager.success('Weather data loaded successfully');
        }
        
        return data;
    } catch (error) {
        console.error('Error fetching weather data:', error);
        
        // Only show error in UI if this is for the current position
        if (isMainWeatherRequest) {
            LoadingManager.hideLoading('weather-info');
            const weatherContainer = document.getElementById('weather-info');
            if (weatherContainer) {
                weatherContainer.innerHTML = '<div class="error-message">Failed to load weather data. Please try again.</div>';
            }
            ToastManager.error('Failed to load weather data: ' + error.message);
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
    
    // Fetch wind barbs if wind overlay is enabled
    const windCheckbox = document.getElementById('wind-overlay');
    if (windCheckbox && windCheckbox.checked) {
        fetchWindBarbs(lat, lon);
    }
}

// Function to fetch comprehensive route weather summary using new API
async function fetchRouteWeatherSummary(routeCoords, cruisingAltitude = 6500) {
    try {
        // Convert route coordinates to waypoints format
        const waypoints = routeCoords.map(coord => ({
            lat: coord[0],
            lon: coord[1]
        }));
        
        ToastManager.info('Fetching route weather analysis...');
        
        const response = await fetch('/api/route_weather_summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                waypoints: waypoints,
                interval_nm: 20,
                altitude_ft: cruisingAltitude
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch route weather summary');
        }
        
        const weatherSummary = await response.json();
        ToastManager.success('Route weather analysis complete');
        return weatherSummary;
        
    } catch (error) {
        console.error('Error fetching route weather summary:', error);
        ToastManager.warning('Could not fetch complete route weather analysis');
        return null;
    }
}

// Function to display route weather summary in UI
function displayRouteWeatherSummary(summary) {
    const summaryContainer = document.getElementById('route-summary');
    if (!summaryContainer) return;
    
    const summaryHtml = `
        <div class="route-weather-summary">
            <h3>Route Weather Summary</h3>
            <div class="weather-summary-grid">
                <div class="weather-stat">
                    <div class="stat-label">Overall Conditions</div>
                    <div class="stat-value ${summary.overall_conditions.toLowerCase()}">${summary.overall_conditions}</div>
                </div>
                <div class="weather-stat">
                    <div class="stat-label">Average Wind</div>
                    <div class="stat-value">${summary.avg_wind_speed_kt} kt</div>
                </div>
                <div class="weather-stat">
                    <div class="stat-label">Max Wind</div>
                    <div class="stat-value">${summary.max_wind_speed_kt} kt</div>
                </div>
                <div class="weather-stat">
                    <div class="stat-label">Min Visibility</div>
                    <div class="stat-value">${summary.min_visibility_sm} sm</div>
                </div>
                <div class="weather-stat">
                    <div class="stat-label">Avg Cloud Cover</div>
                    <div class="stat-value">${summary.avg_cloud_cover_percent}%</div>
                </div>
                <div class="weather-stat">
                    <div class="stat-label">Precip Chance</div>
                    <div class="stat-value">${summary.max_precipitation_probability}%</div>
                </div>
            </div>
            <div class="significant-weather">
                <strong>Significant Weather:</strong>
                <ul>
                    ${summary.significant_weather.map(wx => `<li>${wx}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    
    // Insert after the route stats
    const existingWeatherSummary = summaryContainer.querySelector('.route-weather-summary');
    if (existingWeatherSummary) {
        existingWeatherSummary.remove();
    }
    summaryContainer.insertAdjacentHTML('beforeend', summaryHtml);
}

// Array to store route weather markers
let routeWeatherMarkers = [];

// Function to add weather markers along the route
function addRouteWeatherMarkers(waypointWeather) {
    // Clear existing weather markers
    routeWeatherMarkers.forEach(marker => map.removeLayer(marker));
    routeWeatherMarkers = [];
    
    if (!waypointWeather || waypointWeather.length === 0) return;
    
    // Sample every 3rd waypoint to avoid clutter (approximately every 60nm)
    const sampledWaypoints = waypointWeather.filter((_, index) => index % 3 === 0);
    
    sampledWaypoints.forEach((wp, index) => {
        const flightCategory = determineFlightCategory(wp.visibility_sm, wp.cloud_cover_percent);
        const color = getFlightCategoryColor(flightCategory);
        
        // Create a small weather marker
        const marker = L.circleMarker([wp.lat, wp.lon], {
            radius: 6,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });
        
        // Create tooltip with basic info
        const tooltipContent = `
            <div style="font-size: 11px;">
                <strong>Weather @ ${wp.distance_from_start}nm</strong><br>
                ${flightCategory}<br>
                Wind: ${wp.wind_direction_deg}° @ ${wp.wind_speed_kt}kt<br>
                Vis: ${wp.visibility_sm}sm<br>
                Click route for details
            </div>
        `;
        
        marker.bindTooltip(tooltipContent, {
            permanent: false,
            direction: 'top',
            className: 'route-weather-tooltip'
        });
        
        marker.addTo(map);
        routeWeatherMarkers.push(marker);
    });
}

// Helper function to determine flight category
function determineFlightCategory(visibility_sm, cloud_cover_percent) {
    if (visibility_sm >= 5 && cloud_cover_percent < 50) {
        return 'VFR';
    } else if (visibility_sm >= 3 && cloud_cover_percent < 75) {
        return 'MVFR';
    } else if (visibility_sm >= 1) {
        return 'IFR';
    } else {
        return 'LIFR';
    }
}

// Function to make route polyline clickable for detailed weather
function makeRouteClickable(polyline, cruisingAltitude) {
    if (!polyline) return;
    
    polyline.on('click', async function(e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;
        
        ToastManager.info('Fetching detailed weather...');
        
        try {
            // Fetch detailed weather for the clicked point
            const response = await fetch('/api/point_weather_detail', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    lat: lat,
                    lon: lon,
                    altitude_ft: cruisingAltitude
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch detailed weather');
            }
            
            const detailedWeather = await response.json();
            
            // Display detailed weather in a popup
            displayDetailedWeatherPopup(lat, lon, detailedWeather);
            
            ToastManager.success('Detailed weather loaded');
            
        } catch (error) {
            console.error('Error fetching detailed weather:', error);
            ToastManager.error('Failed to fetch detailed weather');
        }
    });
    
    // Change cursor on hover to indicate it's clickable
    polyline.on('mouseover', function() {
        map.getContainer().style.cursor = 'pointer';
    });
    
    polyline.on('mouseout', function() {
        map.getContainer().style.cursor = '';
    });
}

// Function to display detailed weather popup
function displayDetailedWeatherPopup(lat, lon, weatherData) {
    const current = weatherData.current_conditions;
    const hourly = weatherData.hourly_forecast;
    const winds = weatherData.winds_aloft;
    const clouds = weatherData.cloud_layers;
    
    // Build popup content with detailed aviation weather
    let popupContent = `
        <div class="detailed-weather-popup">
            <h3>Detailed Weather</h3>
            <div class="weather-location">
                ${lat.toFixed(4)}°, ${lon.toFixed(4)}°
            </div>
            
            <div class="current-conditions">
                <h4>Current Conditions</h4>
                <p><strong>${current.weather_description}</strong></p>
                <div class="weather-grid">
                    <div>Temp: ${current.temperature_c}°C (${current.temperature_f}°F)</div>
                    <div>Wind: ${current.wind_direction_deg}° @ ${current.wind_speed_kt}kt</div>
                </div>
            </div>
    `;
    
    // Add winds aloft if available
    if (winds && winds.length > 0) {
        popupContent += `
            <div class="winds-aloft">
                <h4>Winds Aloft</h4>
                <div class="winds-grid">
                    ${winds.map(w => `
                        <div>${w.altitude_ft}ft: ${w.wind_direction_deg}° @ ${w.wind_speed_kt}kt</div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Add cloud layers if available
    if (clouds && clouds.length > 0) {
        popupContent += `
            <div class="cloud-layers">
                <h4>Cloud Layers</h4>
                ${clouds.map(c => `
                    <div>${c.level}: ${c.coverage_percent}% @ ${c.base_ft}ft</div>
                `).join('')}
            </div>
        `;
    }
    
    // Add hourly forecast (next 6 hours)
    if (hourly && hourly.length > 0) {
        const next6Hours = hourly.slice(0, 6);
        popupContent += `
            <div class="hourly-forecast">
                <h4>Next 6 Hours</h4>
                <div class="forecast-grid-compact">
                    ${next6Hours.map(h => {
                        if (!h.time) return '';
                        const time = new Date(h.time * 1000);
                        return `
                            <div class="forecast-hour">
                                <div class="hour-time">${time.getHours().toString().padStart(2, '0')}:00</div>
                                <div class="hour-temp">${h.temperature_c}°C</div>
                                <div class="hour-wind">${h.wind_direction_deg}°/${h.wind_speed_kt}kt</div>
                                <div class="hour-vis">${h.visibility_sm}sm</div>
                                <div class="hour-clouds">${h.cloud_cover_percent}%</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    popupContent += `</div>`;
    
    // Create or update popup
    L.popup({
        maxWidth: 400,
        className: 'detailed-weather-popup-container'
    })
    .setLatLng([lat, lon])
    .setContent(popupContent)
    .openOn(map);
}