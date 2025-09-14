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
  Divider,
} from '@mui/material'
import { Flight, Schedule, Speed, LocalGasStation } from '@mui/icons-material'
import { useQuery } from 'react-query'
import axios from 'axios'
import toast from 'react-hot-toast'

interface FlightPlan {
  departure: string
  destination: string
  route: string[]
  distance: number
  estimated_time: number
  fuel_required: number
  weather_summary: string
}

const FlightPlannerPage: React.FC = () => {
  const [departure, setDeparture] = useState('')
  const [destination, setDestination] = useState('')
  const [aircraft, setAircraft] = useState('')
  const [flightPlan, setFlightPlan] = useState<FlightPlan | null>(null)

  const planFlight = async () => {
    if (!departure || !destination) {
      toast.error('Please enter both departure and destination airports')
      return
    }

    try {
      const response = await axios.post('/api/plan_route', {
        departure,
        destination,
        aircraft_type: aircraft || 'C172'
      })
      setFlightPlan(response.data)
      toast.success('Flight plan generated successfully!')
    } catch (error) {
      toast.error('Failed to generate flight plan')
      console.error('Flight planning error:', error)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <Flight sx={{ mr: 1, verticalAlign: 'middle' }} />
        VFR Flight Planner
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Flight Details
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Departure Airport"
                  placeholder="KPAO"
                  value={departure}
                  onChange={(e) => setDeparture(e.target.value.toUpperCase())}
                  helperText="Enter ICAO or IATA code"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Destination Airport"
                  placeholder="KSQL"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value.toUpperCase())}
                  helperText="Enter ICAO or IATA code"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Aircraft Type"
                  placeholder="C172"
                  value={aircraft}
                  onChange={(e) => setAircraft(e.target.value)}
                  helperText="Optional: Aircraft type for performance calculations"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={planFlight}
                  fullWidth
                  sx={{ mt: 2 }}
                >
                  Generate Flight Plan
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          {flightPlan ? (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Flight Plan Results
              </Typography>
              
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Route: {flightPlan.departure} → {flightPlan.destination}
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    {flightPlan.route.map((waypoint, index) => (
                      <Chip
                        key={index}
                        label={waypoint}
                        variant="outlined"
                        size="small"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Speed sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="body2">
                          Distance: {flightPlan.distance} nm
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Schedule sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="body2">
                          Time: {Math.round(flightPlan.estimated_time)} min
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <LocalGasStation sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="body2">
                          Fuel: {flightPlan.fuel_required.toFixed(1)} gal
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                  
                  {flightPlan.weather_summary && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="body2" color="text.secondary">
                        Weather: {flightPlan.weather_summary}
                      </Typography>
                    </>
                  )}
                </CardContent>
              </Card>
            </Paper>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              <Flight sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
              <Typography variant="h6">
                Enter flight details to generate your VFR flight plan
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default FlightPlannerPage
