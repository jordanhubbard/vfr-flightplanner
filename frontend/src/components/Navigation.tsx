import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Tabs, Tab, Box } from '@mui/material'
import { Flight, Cloud, LocalAirport } from '@mui/icons-material'

const Navigation: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const handleChange = (_event: React.SyntheticEvent, newValue: string) => {
    navigate(newValue)
  }

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Tabs value={location.pathname} onChange={handleChange} centered>
        <Tab 
          icon={<Flight />} 
          label="Flight Planner" 
          value="/" 
        />
        <Tab 
          icon={<Cloud />} 
          label="Weather" 
          value="/weather" 
        />
        <Tab 
          icon={<LocalAirport />} 
          label="Airports" 
          value="/airports" 
        />
      </Tabs>
    </Box>
  )
}

export default Navigation
