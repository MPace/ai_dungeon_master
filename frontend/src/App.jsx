// File: frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import CharacterCreator from './components/CharacterCreator';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router basename="/">
      <div className="App">
        <Routes>
          {/* Dashboard routes - handle multiple possible paths */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/*" element={<Dashboard />} />
          <Route path="/user_dashboard" element={<Dashboard />} />
          <Route path="/game/dashboard" element={<Dashboard />} />
          
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