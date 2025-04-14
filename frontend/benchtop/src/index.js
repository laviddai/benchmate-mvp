// frontend/benchtop/src/index.js
// boots up React application
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './app';
import './styles/global.css'; // optional, if you have global styles

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
