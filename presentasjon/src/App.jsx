import { useState } from 'react'
import { Heading3 } from '@entur/typography'
import DisruptionAlert from './components/DisruptionAlert.jsx'
import disruptionData from './mock/disruption.json'

export default function App() {
  const [selectedAction, setSelectedAction] = useState(null)

  function handleSelect(action, description) {
    setSelectedAction({ action, description, timestamp: new Date().toISOString() })
    console.log('User selected:', { action, description })
  }

  return (
    <div className="app">
      <header className="app-header">
        <Heading3 margin="none">Pendlerkompis</Heading3>
      </header>

      {selectedAction ? (
        <SelectionConfirmation
          selection={selectedAction}
          onUndo={() => setSelectedAction(null)}
        />
      ) : (
        <DisruptionAlert data={disruptionData} onSelect={handleSelect} />
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
