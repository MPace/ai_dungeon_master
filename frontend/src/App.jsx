// File: frontend/src/App.jsx

import React from 'react';
import CharacterCreator from './components/CharacterCreator'; // Import the component we created

import '/app/static/css/styles.css'; 

function App() {
  // The main App component now simply renders our CharacterCreator
  return (
    <div className="App"> {/* Optional: Keep a wrapper div */}
      <CharacterCreator />
    </div>
  );
}

export default App;