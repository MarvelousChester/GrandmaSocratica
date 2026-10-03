import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MantineProvider } from '@mantine/core'
import '@mantine/core/styles.css'
import './styles.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider forceColorScheme="light" theme={{ fontFamily: '"Patrick Hand", sans-serif' }}>
      <App />
    </MantineProvider>
  </StrictMode>,
)
