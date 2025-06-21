# Flight Planner

A comprehensive aviation flight planning application that combines advanced route planning with detailed weather information. Users can plan flights between airports, calculate fuel requirements, visualize weather along routes, and analyze conditions for VFR and IFR operations.

## Features

- Interactive world map
- Airport code search (supports both ICAO and IATA codes)
- Weather forecasts from 1-16 days
- Accurate surface wind conditions with wind direction and gusts
- Weather overlays showing:
  - Clouds
  - Wind speeds
  - Precipitation
  - Temperature
- Real-time updates when selecting different locations
- Airport information within a specified radius
- Detailed weather metrics including:
  - Temperature
  - Wind conditions
  - Visibility
  - Cloud cover
  - Pressure
  - Precipitation probability

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- OpenWeatherMap API key

## API Key Setup

1. Get a free OpenWeatherMap API key:
   - Visit [OpenWeatherMap](https://openweathermap.org/api)
   - Sign up for a free account
   - Navigate to "My API Keys" in your account
   - Copy your API key

2. Create a `.env` file in the project root:

   ```bash
   touch .env
   ```

3. Add your API key to the `.env` file:

   ```text
   OPENWEATHERMAP_API_KEY=your_api_key_here
   ```

## Installation

### Local Installation

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd weather-forecasts
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate

   # On Windows:
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Docker Installation

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd weather-forecasts
   ```

2. Build and run with Docker:

   ```bash
   # Using Docker Compose (recommended)
   docker compose up -d
   ```

## Running the Application

### Running the Application

Running the application locally via Python/venv is no longer supported. Always use Docker Compose.

1. Start the application using Docker Compose:

   ```bash
   # Run on default port 8080 (Docker only)
   make run

   # Or specify a custom port
   make run PORT=5070
   ```

2. Open your browser and navigate to:
   - Default: `http://localhost:8080`
   - Custom port: `http://localhost:PORT` (replace PORT with your specified port number)

### Docker Execution

1. Run using Docker Compose:

   ```bash
   make compose-up
   ```

2. View logs:

   ```bash
   make compose-logs
   ```

3. Stop the container:

   ```bash
   make compose-down
   ```

4. Open your browser and navigate to `http://localhost:8080`

## Usage

- **Map Selection**: Click anywhere on the map to get weather information for that location
- **Airport Search**: Enter an airport code (e.g., KPAO for Palo Alto Airport) in the search box
- **Forecast Days**: Adjust the slider to see forecasts for different number of days
- **Weather Overlays**: Toggle different weather overlays using the checkboxes
- **Overlay Opacity**: Adjust the opacity of weather overlays using the slider

## Airport Search Examples

The application supports both ICAO (4-letter) and IATA (3-letter) airport codes. Here are some common examples:

Major Airports:

- KSFO / SFO - San Francisco International Airport
- KLAX / LAX - Los Angeles International Airport
- KJFK / JFK - John F. Kennedy International Airport
- EGLL / LHR - London Heathrow Airport
- LFPG / CDG - Paris Charles de Gaulle Airport

Regional/General Aviation:

- KPAO / PAO - Palo Alto Airport
- KRHV / RHV - Reid-Hillview Airport
- KSQL / SQL - San Carlos Airport

Tips for Airport Search:

- ICAO codes in the United States typically start with 'K' followed by the IATA code
- Canadian airports typically start with 'C'
- European airports often start with 'E' (UK: 'EG', Germany: 'ED', France: 'LF')
- If one code doesn't work, try the alternative (ICAO or IATA)
- The search is case-insensitive, so 'kpao' and 'KPAO' will work the same

## Technologies Used

- Backend:
  - Flask (Python web framework)
  - Open-Meteo API (weather data)
  - OpenWeatherMap API (additional weather data and overlays)
  - python-dotenv (environment management)
  
- Frontend:
  - Leaflet.js (interactive maps)
  - HTML/CSS/JavaScript
  - Modern responsive design

## API Usage Notes

- The OpenWeatherMap API key is required for weather overlays and additional data
- The free tier of OpenWeatherMap API has the following limits:
  - 60 calls/minute
  - 1,000,000 calls/month
- Open-Meteo API is used for core weather data and does not require authentication

## Troubleshooting

- If you see "API key not configured" error, check your `.env` file
- If weather overlays don't load, verify your OpenWeatherMap API key is valid
- For airport searches, try both ICAO (e.g., KPAO) and IATA (e.g., PAO) codes

## License

This project is licensed under the MIT License - see the LICENSE file for details