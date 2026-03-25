import { useState } from 'react'
import { PrimaryButton } from '@entur/button'
import { Paragraph } from '@entur/typography'
import { SmallAlertBox } from '@entur/alert'
import useNotification from '../hooks/useNotification.js'

const buttonStyle = {
  width: '100%',
  padding: '0.75rem 1rem',
  fontSize: '0.95rem',
  border: '2px solid var(--colors-brand-blue, #181c56)',
  borderRadius: '8px',
  background: 'white',
  color: 'var(--colors-brand-blue, #181c56)',
  cursor: 'pointer',
  textAlign: 'left',
}

export default function NotificationPrompt({ onSimulateDisruption }) {
  const { permission, isSupported, requestPermission, sendNotification } = useNotification()
  const [simulated, setSimulated] = useState(false)

  async function handleEnable() {
    const result = await requestPermission()
    if (result === 'granted') {
      console.log('[Demo] Notifications enabled.')
    }
  }

  function handleSimulate(caseId, title, body) {
    setSimulated(caseId)
    sendNotification(title, body)
    setTimeout(() => {
      onSimulateDisruption?.(caseId)
    }, 1000)
  }

  if (!isSupported) {
    return (
      <SmallAlertBox variant="info">
        Nettleseren din støtter ikke varsler.
      </SmallAlertBox>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {permission === 'default' && (
        <PrimaryButton onClick={handleEnable} style={{ width: '100%' }}>
          Slå på varsler
        </PrimaryButton>
      )}

      {permission === 'granted' && (
        <>
          <SmallAlertBox variant="success">
            Varsler er aktivert
          </SmallAlertBox>
          <button
            onClick={() => handleSimulate(
              'case1',
              'Avvik på hjemreisen din',
              'Signalfeil på Brynseng. T-bane linje 2 kjører ikke som planlagt.'
            )}
            disabled={!!simulated}
            style={buttonStyle}
          >
            Simuler: T-bane stopp (Jernbanetorget → Smestad)
          </button>
          <button
            onClick={() => handleSimulate(
              'case2',
              'Avvik på hjemreisen din',
              'E18/Mosseveien er stengt. Buss 500 til Drøbak går ikke.'
            )}
            disabled={!!simulated}
            style={buttonStyle}
          >
            Simuler: E18 stengt (Bjørvika → Drøbak)
          </button>
          <Paragraph style={{ fontSize: '0.85rem', color: '#666' }}>
            Sjekk at nettleseren har tillatelse i Systeminnstillinger &gt; Varsler hvis notifikasjonen ikke vises.
          </Paragraph>
        </>
      )}

      {permission === 'denied' && (
        <SmallAlertBox variant="negative">
          Varsler er blokkert. Endre i nettleserinnstillingene.
        </SmallAlertBox>
      )}
    </div>
  )
}
