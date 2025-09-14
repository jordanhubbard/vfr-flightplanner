import React, { useState } from 'react'
import {
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Card,
  CardContent,
  Box,
  Chip,
} from '@mui/material'
import { Cloud, Thermostat, Air, Visibility } from '@mui/icons-material'
import { useQuery } from 'react-query'
import axios from 'axios'
import toast from 'react-hot-toast'

interface WeatherData {
  airport: string
  conditions: string
  temperature: number
  wind_speed: number
  wind_direction: number
  visibility: number
  ceiling: number
  metar: string
}

const WeatherPage: React.FC = () => {
  const [airport, setAirport] = useState('')
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null)

  const getWeather = async () => {
    if (!airport) {
      toast.error('Please enter an airport code')
      return
    }

    try {
      const response = await axios.get(`/api/weather/${airport}`)
      setWeatherData(response.data)
      toast.success('Weather data retrieved successfully!')
    } catch (error) {
      toast.error('Failed to get weather data')
      console.error('Weather error:', error)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <Cloud sx={{ mr: 1, verticalAlign: 'middle' }} />
        Weather Information
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Airport Weather
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Airport Code"
                  placeholder="KPAO"
                  value={airport}
                  onChange={(e) => setAirport(e.target.value.toUpperCase())}
                  helperText="Enter ICAO or IATA code"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={getWeather}
                  fullWidth
                  sx={{ mt: 2 }}
                >
                  Get Weather
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          {weatherData ? (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Current Weather - {weatherData.airport}
              </Typography>
              
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {weatherData.conditions}
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Thermostat sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="body1">
                          {weatherData.temperature}°F
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Air sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="body1">
                          {weatherData.wind_direction}° @ {weatherData.wind_speed} kts
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Visibility sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="body1">
                          {weatherData.visibility} SM
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Cloud sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="body1">
                          {weatherData.ceiling} ft
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                  
                  {weatherData.metar && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        METAR:
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {weatherData.metar}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Paper>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              <Cloud sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
              <Typography variant="h6">
                Enter an airport code to get current weather conditions
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default WeatherPage
