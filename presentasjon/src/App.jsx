import { useState, useEffect } from 'react'
import { Heading3 } from '@entur/typography'
import DisruptionAlert from './components/DisruptionAlert.jsx'

const API_URL = 'http://localhost:8000/api/anbefaling?direction=fra_jobb'

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedAction, setSelectedAction] = useState(null)

  useEffect(() => {
    fetch(API_URL)
      .then(res => res.json())
      .then(json => { setData(json); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  function handleSelect(action, description) {
    setSelectedAction({ action, description, timestamp: new Date().toISOString() })
    console.log('User selected:', { action, description })
  }

  function handleRefresh() {
    setLoading(true)
    setError(null)
    setSelectedAction(null)
    fetch(API_URL)
      .then(res => res.json())
      .then(json => { setData(json); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }

  return (
    <div className="app">
      <header className="app-header">
        <Heading3 margin="none">Pendlerkompis</Heading3>
      </header>

      {loading && <p style={{ textAlign: 'center', padding: '2rem' }}>Henter reisedata...</p>}
      {error && <p style={{ textAlign: 'center', padding: '2rem', color: 'red' }}>Feil: {error}</p>}

      {!loading && !error && data && (
        selectedAction ? (
          <SelectionConfirmation
            selection={selectedAction}
            onUndo={() => setSelectedAction(null)}
          />
        ) : (
          <>
            <DisruptionAlert data={data} onSelect={handleSelect} />
            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <button onClick={handleRefresh} style={{
                padding: '0.5rem 1rem', background: 'none',
                border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer'
              }}>
                Oppdater
              </button>
            </div>
          </>
        )
      )}
    </div>
  )
}

function SelectionConfirmation({ selection, onUndo }) {
  return (
    <div style={{ textAlign: 'center', padding: '2rem 0' }}>
      <Heading3>Du valgte:</Heading3>
      <p style={{ marginTop: '1rem', fontSize: '1.1rem' }}>
        {selection.description}
      </p>
      <button
        onClick={onUndo}
        style={{
          marginTop: '1.5rem',
          padding: '0.5rem 1rem',
          background: 'none',
          border: '1px solid #ccc',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        Angre
      </button>
    </div>
  )
}
