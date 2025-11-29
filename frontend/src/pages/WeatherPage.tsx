import React, { useState } from 'react'
import { Grid, TextField, Card, CardContent, Box } from '@mui/material'
import { Cloud, Thermostat, Air, Visibility } from '@mui/icons-material'
import toast from 'react-hot-toast'
import { 
  PageHeader, 
  FormSection, 
  EmptyState, 
  LoadingState, 
  ResultsSection 
} from '../components/shared'
import { useApiMutation } from '../hooks'
import { weatherService } from '../services'
import { validateAirportCode } from '../utils'
import type { WeatherData } from '../types'

const WeatherPage: React.FC = () => {
  const [airport, setAirport] = useState('')
  const [validationError, setValidationError] = useState<string>('')

  const weatherMutation = useApiMutation<WeatherData, string>(
    (airportCode) => weatherService.getWeather(airportCode),
    {
      successMessage: 'Weather data retrieved successfully!',
    }
  )

  const getWeather = () => {
    const validation = validateAirportCode(airport)
    if (!validation.valid) {
      setValidationError(validation.error || '')
      toast.error(validation.error || 'Invalid airport code')
      return
    }
    
    setValidationError('')
    weatherMutation.mutate(airport.toUpperCase())
  }

  const handleAirportChange = (value: string) => {
    setAirport(value.toUpperCase())
    if (validationError) {
      setValidationError('')
    }
  }

  const weatherData = weatherMutation.data

  return (
    <Box>
      <PageHeader icon={<Cloud />} title="Weather Information" />
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <FormSection
            title="Airport Weather"
            onSubmit={getWeather}
            buttonText="Get Weather"
            isLoading={weatherMutation.isLoading}
          >
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Airport Code"
                placeholder="KPAO"
                value={airport}
                onChange={(e) => handleAirportChange(e.target.value)}
                helperText={validationError || "Enter ICAO or IATA code"}
                error={!!validationError}
                disabled={weatherMutation.isLoading}
              />
            </Grid>
          </FormSection>
        </Grid>
        
        <Grid item xs={12} md={6}>
          {weatherMutation.isLoading ? (
            <LoadingState message="Fetching weather data..." />
          ) : weatherData ? (
            <ResultsSection title={`Current Weather - ${weatherData.airport}`}>
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Box variant="h6" component="div" gutterBottom>
                    {weatherData.conditions}
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Thermostat sx={{ mr: 1, color: 'primary.main' }} />
                        <Box component="span" variant="body1">
                          {weatherData.temperature}°F
                        </Box>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Air sx={{ mr: 1, color: 'primary.main' }} />
                        <Box component="span" variant="body1">
                          {weatherData.wind_direction}° @ {weatherData.wind_speed} kts
                        </Box>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Visibility sx={{ mr: 1, color: 'primary.main' }} />
                        <Box component="span" variant="body1">
                          {weatherData.visibility} SM
                        </Box>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Cloud sx={{ mr: 1, color: 'primary.main' }} />
                        <Box component="span" variant="body1">
                          {weatherData.ceiling} ft
                        </Box>
                      </Box>
                    </Grid>
                  </Grid>
                  
                  {weatherData.metar && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Box component="span" variant="caption" color="text.secondary">
                        METAR:
                      </Box>
                      <Box component="div" variant="body2" sx={{ fontFamily: 'monospace', mt: 1 }}>
                        {weatherData.metar}
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </ResultsSection>
          ) : (
            <EmptyState
              icon={<Cloud />}
              message="Enter an airport code to get current weather conditions"
            />
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default WeatherPage
