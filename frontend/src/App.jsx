// File: frontend/src/App.jsx

import React from 'react';
import CharacterCreator from './components/CharacterCreator';
import Dashboard from './components/Dashboard';

function App() {
  // Check if the current page is the dashboard or character creation
  const path = window.location.pathname;
  
  // For the dashboard route, we need to match /dashboard or /user_dashboard or /game/dashboard
  const isDashboard = path.includes('/dashboard') || path.includes('/user_dashboard');
  // For character creation, we need to match /characters/create
  const isCharacterCreation = path.includes('/characters/create');
  
  if (isDashboard) {
    return <Dashboard />;
  }
  
  if (isCharacterCreation) {
    return <CharacterCreator />;
  }
  
  // If no route matches, show a simple message
  return (
    <div className="App">
      <div style={{color: 'white', textAlign: 'center', marginTop: '100px'}}>
        Unknown route. Please navigate to the dashboard.
      </div>
    </div>
  );
}

export default App;