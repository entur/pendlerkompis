import { useState, useEffect } from 'react'
import { Heading3, Paragraph } from '@entur/typography'
import { SmallAlertBox } from '@entur/alert'
import DisruptionAlert from './components/DisruptionAlert.jsx'
import NotificationPrompt from './components/NotificationPrompt.jsx'
import useMotorApi from './hooks/useMotorApi.js'
import useNotification from './hooks/useNotification.js'
import case1Data from './mock/disruption-case1.json'
import case2Data from './mock/disruption-case2.json'

const isDemoMode = new URLSearchParams(window.location.search).has('demo')

const mockCases = { case1: case1Data, case2: case2Data }

export default function App() {
  const [selectedAction, setSelectedAction] = useState(null)
  const [activeCase, setActiveCase] = useState(null)
  const motor = useMotorApi()
  const { permission, sendNotification } = useNotification()
  const [notifiedAvvikId, setNotifiedAvvikId] = useState(null)

  // Send notification when motor detects a new disruption
  useEffect(() => {
    if (!motor.recommendation) return
    const avvikIds = motor.recommendation.situasjon?.avvik_ids?.join(',')
    if (avvikIds && avvikIds !== notifiedAvvikId && permission === 'granted') {
      sendNotification(
        'Avvik på hjemreisen din',
        motor.recommendation.situasjon.oppsummering
      )
      setNotifiedAvvikId(avvikIds)
    }
  }, [motor.recommendation, notifiedAvvikId, permission, sendNotification])


  function handleSelect(action, description, alternativId) {
    setSelectedAction({ action, description, timestamp: new Date().toISOString() })
    motor.sendFeedback(action, alternativId)
    console.log('User selected:', { action, description })
  }

  function handleSimulateDisruption(caseId) {
    setSelectedAction(null)
    setActiveCase(caseId)
  }

  function handleReset() {
    setSelectedAction(null)
    setActiveCase(null)
    setNotifiedAvvikId(null)
  }

  // Determine which data to show
  const activeData = isDemoMode
    ? (activeCase ? mockCases[activeCase] : null)
    : motor.recommendation

  return (
    <div className="app">
      <header className="app-header">
        <Heading3 margin="none">Pendlerkompis</Heading3>
      </header>

      {selectedAction ? (
        <SelectionConfirmation selection={selectedAction} onUndo={handleReset} />
      ) : activeData ? (
        <DisruptionAlert data={activeData} onSelect={handleSelect} />
      ) : (
        <HomeScreen
          isDemoMode={isDemoMode}
          motorError={motor.error}
          isLoading={motor.isLoading}
          onRefresh={motor.refresh}
          onSimulateDisruption={handleSimulateDisruption}
        />
      )}
    </div>
  )
}

function HomeScreen({ isDemoMode, motorError, isLoading, onRefresh, onSimulateDisruption }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{
        textAlign: 'center',
        padding: '2rem 0',
        borderBottom: '1px solid var(--colors-greys-grey10, #eee)',
      }}>
        <Paragraph>Ingen avvik på reisen din akkurat nå.</Paragraph>
        {!isDemoMode && (
          <button
            onClick={onRefresh}
            disabled={isLoading}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1.25rem',
              background: 'none',
              border: '1px solid #ccc',
              borderRadius: '4px',
              cursor: isLoading ? 'default' : 'pointer',
              color: '#555',
            }}
          >
            {isLoading ? 'Sjekker...' : 'Sjekk nå'}
          </button>
        )}
      </div>

      {!isDemoMode && motorError && (
        <SmallAlertBox variant="warning">
          Kan ikke nå motoren ({motorError})
        </SmallAlertBox>
      )}

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
