import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Failed to find the root element')

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e1b4b',
            color: '#e0e7ff',
            borderRadius: '12px',
            fontWeight: '500',
          },
          success: {
            duration: 3000,
            style: { background: '#14532d', color: '#dcfce7' },
          },
          error: {
            duration: 5000,
            style: { background: '#7f1d1d', color: '#fecaca' },
          },
        }}
      />
      <App />
    </BrowserRouter>
  </StrictMode>,
)
