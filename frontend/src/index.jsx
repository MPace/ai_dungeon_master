// File: frontend/src/index.jsx

import React from 'react';
import ReactDOM from 'react-dom/client'; // Use react-dom/client for React 18+
import App from './App.jsx';             // Import the main App component
import './index.css';                 // Import the basic CSS file we created

// Find the root element in your public/index.html or Flask template
const rootElement = document.getElementById('root');

if (rootElement) {
  // Create a root and render the App component into it
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode> {/* StrictMode helps catch potential problems */}
      <App />
    </React.StrictMode>
  );
} else {
  console.error('Failed to find the root element. Make sure your HTML has <div id="root"></div>');
}