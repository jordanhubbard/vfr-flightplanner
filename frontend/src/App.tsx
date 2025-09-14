import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material'
import FlightPlannerPage from './pages/FlightPlannerPage'
import WeatherPage from './pages/WeatherPage'
import AirportsPage from './pages/AirportsPage'
import Navigation from './components/Navigation'

function App() {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ✈️ VFR Flight Planner
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Navigation />
      
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<FlightPlannerPage />} />
          <Route path="/weather" element={<WeatherPage />} />
          <Route path="/airports" element={<AirportsPage />} />
        </Routes>
      </Container>
    </Box>
  )
}

export default App
