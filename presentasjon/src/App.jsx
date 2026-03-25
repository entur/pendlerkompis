import { useState, useEffect } from 'react'
import { Heading3, Paragraph } from '@entur/typography'
import { SmallAlertBox } from '@entur/alert'
import DisruptionAlert from './components/DisruptionAlert.jsx'
import NotificationPrompt from './components/NotificationPrompt.jsx'
import useMotorApi from './hooks/useMotorApi.js'
import useNotification from './hooks/useNotification.js'
import disruptionData from './mock/disruption.json'

const isDemoMode = new URLSearchParams(window.location.search).has('demo')

export default function App() {
  const [selectedAction, setSelectedAction] = useState(null)
  const [showMockDisruption, setShowMockDisruption] = useState(false)
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

  // Stop polling when user has made a selection
  useEffect(() => {
    if (selectedAction) {
      motor.stopPolling()
    } else if (!isDemoMode) {
      motor.startPolling()
    }
  }, [selectedAction])

  function handleSelect(action, description, alternativId) {
    setSelectedAction({ action, description, timestamp: new Date().toISOString() })
    motor.sendFeedback(action, alternativId)
    console.log('User selected:', { action, description })
  }

  function handleReset() {
    setSelectedAction(null)
    setShowMockDisruption(false)
    setNotifiedAvvikId(null)
  }

  // Determine which data to show
  const activeData = isDemoMode
    ? (showMockDisruption ? disruptionData : null)
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
          onSimulateDisruption={() => setShowMockDisruption(true)}
        />
      )}
    </div>
  )
}

function HomeScreen({ isDemoMode, motorError, onSimulateDisruption }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{
        textAlign: 'center',
        padding: '2rem 0',
        borderBottom: '1px solid var(--colors-greys-grey10, #eee)',
      }}>
        <Paragraph>Ingen avvik på reisen din akkurat nå.</Paragraph>
        {!isDemoMode && (
          <Paragraph style={{ fontSize: '0.8rem', color: '#999', marginTop: '0.5rem' }}>
            Sjekker hvert 10. sekund...
          </Paragraph>
        )}
      </div>

      {!isDemoMode && motorError && (
        <SmallAlertBox variant="warning">
          Kan ikke nå motoren ({motorError}). Prøver igjen...
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
