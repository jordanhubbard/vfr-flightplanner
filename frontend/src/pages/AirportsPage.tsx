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
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import { LocalAirport, Search, LocationOn } from '@mui/icons-material'
import { useQuery } from 'react-query'
import axios from 'axios'
import toast from 'react-hot-toast'

interface Airport {
  icao: string
  iata: string
  name: string
  city: string
  country: string
  latitude: number
  longitude: number
  elevation: number
  type: string
}

const AirportsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [airports, setAirports] = useState<Airport[]>([])
  const [selectedAirport, setSelectedAirport] = useState<Airport | null>(null)

  const searchAirports = async () => {
    if (!searchTerm) {
      toast.error('Please enter a search term')
      return
    }

    try {
      const response = await axios.get(`/api/airports/search?q=${searchTerm}`)
      setAirports(response.data)
      toast.success(`Found ${response.data.length} airports`)
    } catch (error) {
      toast.error('Failed to search airports')
      console.error('Airport search error:', error)
    }
  }

  const getAirportDetails = async (icao: string) => {
    try {
      const response = await axios.get(`/api/airports/${icao}`)
      setSelectedAirport(response.data)
    } catch (error) {
      toast.error('Failed to get airport details')
      console.error('Airport details error:', error)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <LocalAirport sx={{ mr: 1, verticalAlign: 'middle' }} />
        Airport Information
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Search Airports
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Search"
                  placeholder="Airport name, city, or code"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  helperText="Enter airport name, city, or ICAO/IATA code"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={searchAirports}
                  fullWidth
                  sx={{ mt: 2 }}
                  startIcon={<Search />}
                >
                  Search Airports
                </Button>
              </Grid>
            </Grid>
            
            {airports.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Search Results ({airports.length})
                </Typography>
                <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {airports.map((airport) => (
                    <ListItem
                      key={airport.icao}
                      button
                      onClick={() => getAirportDetails(airport.icao)}
                      sx={{ 
                        border: 1, 
                        borderColor: 'divider', 
                        borderRadius: 1, 
                        mb: 1 
                      }}
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle1">
                              {airport.name}
                            </Typography>
                            <Chip 
                              label={airport.icao} 
                              size="small" 
                              variant="outlined" 
                            />
                            {airport.iata && (
                              <Chip 
                                label={airport.iata} 
                                size="small" 
                                variant="outlined" 
                              />
                            )}
                          </Box>
                        }
                        secondary={`${airport.city}, ${airport.country}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          {selectedAirport ? (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Airport Details
              </Typography>
              
              <Card>
                <CardContent>
                  <Typography variant="h5" gutterBottom>
                    {selectedAirport.name}
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Chip 
                      label={selectedAirport.icao} 
                      color="primary" 
                      sx={{ mr: 1 }} 
                    />
                    {selectedAirport.iata && (
                      <Chip 
                        label={selectedAirport.iata} 
                        color="secondary" 
                        sx={{ mr: 1 }} 
                      />
                    )}
                    <Chip 
                      label={selectedAirport.type} 
                      variant="outlined" 
                    />
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <LocationOn sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="body1">
                          {selectedAirport.city}, {selectedAirport.country}
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Latitude
                      </Typography>
                      <Typography variant="body1">
                        {selectedAirport.latitude.toFixed(6)}°
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Longitude
                      </Typography>
                      <Typography variant="body1">
                        {selectedAirport.longitude.toFixed(6)}°
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Elevation
                      </Typography>
                      <Typography variant="body1">
                        {selectedAirport.elevation} ft
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Paper>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              <LocalAirport sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
              <Typography variant="h6">
                Search for airports and select one to view details
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default AirportsPage
