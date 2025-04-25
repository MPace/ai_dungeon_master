// File: frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import CharacterCreator from './components/CharacterCreator';
import Dashboard from './components/Dashboard';

function App() {
  // Check if the current page is the dashboard or character creation
  const path = window.location.pathname;
  
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Dashboard route */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/user_dashboard" element={<Navigate to="/dashboard" replace />} />
          
          {/* Character creation route */}
          <Route path="/characters/create" element={<CharacterCreator />} />
          
          {/* Default redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;