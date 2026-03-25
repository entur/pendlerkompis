import React from 'react'
import ReactDOM from 'react-dom/client'
import '@entur/tokens/dist/styles.css'
import '@entur/typography/dist/styles.css'
import '@entur/alert/dist/styles.css'
import '@entur/button/dist/styles.css'
import '@entur/layout/dist/styles.css'
import App from './App.jsx'
import './app.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// Register service worker for PWA support
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
  })
}
