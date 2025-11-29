import React, { useState } from 'react'
import {
  Grid,
  TextField,
  Card,
  CardContent,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  Typography,
} from '@mui/material'
import { LocalAirport, Search, LocationOn } from '@mui/icons-material'
import toast from 'react-hot-toast'
import { 
  PageHeader, 
  FormSection, 
  EmptyState, 
  LoadingState, 
  ResultsSection 
} from '../components/shared'
import { useApiMutation } from '../hooks'
import { airportService } from '../services'
import { validateRequired } from '../utils'
import type { Airport } from '../types'

const AirportsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIcao, setSelectedIcao] = useState<string>('')
  const [searchError, setSearchError] = useState<string>('')

  const searchMutation = useApiMutation<Airport[], string>(
    (query) => airportService.search(query),
    {
      successMessage: undefined, // Custom message after success
      onSuccess: (data) => {
        toast.success(`Found ${data.length} airport${data.length !== 1 ? 's' : ''}`)
      },
    }
  )

  const detailsMutation = useApiMutation<Airport, string>(
    (icao) => airportService.getDetails(icao)
  )

  const handleSearch = () => {
    const validation = validateRequired(searchTerm, 'Search term')
    if (!validation.valid) {
      setSearchError(validation.error || '')
      toast.error(validation.error || 'Invalid search term')
      return
    }

    setSearchError('')
    setSelectedIcao('')
    searchMutation.mutate(searchTerm)
  }

  const handleSelectAirport = (icao: string) => {
    setSelectedIcao(icao)
    detailsMutation.mutate(icao)
  }

  const handleSearchTermChange = (value: string) => {
    setSearchTerm(value)
    if (searchError) setSearchError('')
  }

  const airports = searchMutation.data || []
  const selectedAirport = detailsMutation.data

  return (
    <Box>
      <PageHeader icon={<LocalAirport />} title="Airport Information" />
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <FormSection
            title="Search Airports"
            onSubmit={handleSearch}
            buttonText="Search Airports"
            isLoading={searchMutation.isLoading}
          >
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Search"
                placeholder="Airport name, city, or code"
                value={searchTerm}
                onChange={(e) => handleSearchTermChange(e.target.value)}
                helperText={searchError || "Enter airport name, city, or ICAO/IATA code"}
                error={!!searchError}
                disabled={searchMutation.isLoading}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'action.disabled' }} />,
                }}
              />
            </Grid>
          </FormSection>
            
          {searchMutation.isLoading ? (
            <Box sx={{ mt: 3 }}>
              <LoadingState message="Searching airports..." />
            </Box>
          ) : airports.length > 0 ? (
            <Box sx={{ mt: 3 }}>
              <ResultsSection title={`Search Results (${airports.length})`}>
                <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {airports.map((airport) => (
                    <ListItem
                      key={airport.icao}
                      component="button"
                      onClick={() => handleSelectAirport(airport.icao)}
                      sx={{ 
                        border: 1, 
                        borderColor: 'divider', 
                        borderRadius: 1, 
                        mb: 1,
                        cursor: 'pointer',
                        '&:hover': {
                          bgcolor: 'action.hover',
                        },
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
              </ResultsSection>
            </Box>
          ) : null}
        </Grid>
        
        <Grid item xs={12} md={6}>
          {detailsMutation.isLoading ? (
            <LoadingState message="Loading airport details..." />
          ) : selectedAirport ? (
            <ResultsSection title="Airport Details">
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
            </ResultsSection>
          ) : (
            <EmptyState
              icon={<LocalAirport />}
              message="Search for airports and select one to view details"
            />
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default AirportsPage
