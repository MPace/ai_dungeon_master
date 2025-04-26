// File: frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
  
  // Only render the router if we're not handling a special case above
  // This avoids React Router's base path issues when the app is mounted at a non-root URL
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Default redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;