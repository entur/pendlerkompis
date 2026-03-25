import { useState } from 'react'
import { Heading3, Paragraph } from '@entur/typography'
import DisruptionAlert from './components/DisruptionAlert.jsx'
import NotificationPrompt from './components/NotificationPrompt.jsx'
import disruptionData from './mock/disruption.json'

const isDemoMode = new URLSearchParams(window.location.search).has('demo')

export default function App() {
  const [selectedAction, setSelectedAction] = useState(null)
  const [showDisruption, setShowDisruption] = useState(false)

  function handleSelect(action, description) {
    setSelectedAction({ action, description, timestamp: new Date().toISOString() })
    console.log('User selected:', { action, description })
  }

  function handleSimulateDisruption() {
    setSelectedAction(null)
    setShowDisruption(true)
  }

  function handleReset() {
    setSelectedAction(null)
    setShowDisruption(false)
  }

  return (
    <div className="app">
      <header className="app-header">
        <Heading3 margin="none">Pendlerkompis</Heading3>
      </header>

      {selectedAction ? (
        <SelectionConfirmation
          selection={selectedAction}
          onUndo={handleReset}
        />
      ) : showDisruption ? (
        <DisruptionAlert data={disruptionData} onSelect={handleSelect} />
      ) : (
        <HomeScreen onSimulateDisruption={handleSimulateDisruption} />
      )}
    </div>
  )
}

function HomeScreen({ onSimulateDisruption }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{
        textAlign: 'center',
        padding: '2rem 0',
        borderBottom: '1px solid var(--colors-greys-grey10, #eee)',
      }}>
        <Paragraph>Ingen avvik på reisen din akkurat nå.</Paragraph>
      </div>

      {isDemoMode && (
        <NotificationPrompt onSimulateDisruption={onSimulateDisruption} />
      )}
    </div>
  )
}

function SelectionConfirmation({ selection, onUndo }) {
  return (
    <div style={{ textAlign: 'center', padding: '2rem 0' }}>
      <Heading3>Du valgte:</Heading3>
      <Paragraph style={{ marginTop: '1rem' }}>
        {selection.description}
      </Paragraph>
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
        Tilbake
      </button>
    </div>
  )
}
