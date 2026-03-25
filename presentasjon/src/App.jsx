import { useState, useEffect, useRef } from 'react'
import { Heading3 } from '@entur/typography'
import DisruptionAlert from './components/DisruptionAlert.jsx'

const STREAM_URL = 'http://localhost:8000/api/stream?direction=fra_jobb'

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedAction, setSelectedAction] = useState(null)
  const [paused, setPaused] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const pausedRef = useRef(false)

  useEffect(() => {
    pausedRef.current = paused
  }, [paused])

  useEffect(() => {
    const source = new EventSource(STREAM_URL)

    source.addEventListener('anbefaling', (event) => {
      if (pausedRef.current) return
      try {
        const json = JSON.parse(event.data)
        setData(json)
        setLoading(false)
        setError(null)
        setLastUpdate(new Date())
      } catch (e) {
        console.error('Parse error:', e)
      }
    })

    source.addEventListener('error', (event) => {
      if (event.data) {
        try {
          const err = JSON.parse(event.data)
          setError(err.error || 'Ukjent feil')
        } catch { /* ignore */ }
      }
    })

    source.onerror = () => {
      setError('Mista kontakt med motor-server. Proevar aa koble til paa nytt...')
      setLoading(false)
    }

    return () => source.close()
  }, [])

  function handleSelect(action, description) {
    setSelectedAction({ action, description, timestamp: new Date().toISOString() })
    setPaused(true)
    console.log('User selected:', { action, description })
  }

  function handleUndo() {
    setSelectedAction(null)
    setPaused(false)
  }

  const typeLabel = data?.type === 'avvik' ? '⚠️ Avvik' : '✅ Vaermelding'
  const timeStr = lastUpdate ? lastUpdate.toLocaleTimeString('nb-NO') : ''

  return (
    <div className="app">
      <header className="app-header">
        <Heading3 margin="none">Pendlerkompis</Heading3>
        {data && (
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', fontSize: '0.85rem', color: '#666' }}>
            <span>{typeLabel}</span>
            <span>Oppdatert {timeStr}</span>
            {!selectedAction && (
              <button
                onClick={() => setPaused(p => !p)}
                style={{
                  padding: '0.25rem 0.5rem', background: paused ? '#fff3cd' : 'none',
                  border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem'
                }}
              >
                {paused ? '▶ Fortsett' : '⏸ Pause'}
              </button>
            )}
          </div>
        )}
      </header>

      {loading && <p style={{ textAlign: 'center', padding: '2rem' }}>Kobler til motor-server...</p>}
      {error && <p style={{ textAlign: 'center', padding: '2rem', color: 'red' }}>Feil: {error}</p>}

      {!loading && !error && data && (
        selectedAction ? (
          <SelectionConfirmation
            selection={selectedAction}
            onUndo={handleUndo}
          />
        ) : (
          <DisruptionAlert data={data} onSelect={handleSelect} />
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
        Angre (fortset live-oppdateringar)
      </button>
    </div>
  )
}
