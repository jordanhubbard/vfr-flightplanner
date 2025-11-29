import React, { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material'
import Navigation from './components/Navigation'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LoadingState } from './components/shared'

// Code splitting with React.lazy for better performance
const FlightPlannerPage = lazy(() => import('./pages/FlightPlannerPage'))
const WeatherPage = lazy(() => import('./pages/WeatherPage'))
const AirportsPage = lazy(() => import('./pages/AirportsPage'))

function App() {
  return (
    <ErrorBoundary>
      <Box sx={{ flexGrow: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppBar position="static" component="header" role="banner">
          <Toolbar>
            <Typography variant="h6" component="h1" sx={{ flexGrow: 1 }}>
              ✈️ VFR Flight Planner
            </Typography>
          </Toolbar>
        </AppBar>
        
        <Navigation />
        
        <Container 
          maxWidth="xl" 
          sx={{ mt: 4, mb: 4, flex: 1 }} 
          component="main" 
          role="main"
        >
          <Suspense fallback={<LoadingState message="Loading page..." />}>
            <Routes>
              <Route path="/" element={<FlightPlannerPage />} />
              <Route path="/weather" element={<WeatherPage />} />
              <Route path="/airports" element={<AirportsPage />} />
            </Routes>
          </Suspense>
        </Container>
      </Box>
    </ErrorBoundary>
  )
}

export default App
