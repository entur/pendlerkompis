import { useState } from 'react'
import { PrimaryButton, SecondaryButton } from '@entur/button'
import { Paragraph } from '@entur/typography'
import { SmallAlertBox } from '@entur/alert'
import useNotification from '../hooks/useNotification.js'
import disruptionData from '../mock/disruption.json'

export default function NotificationPrompt({ onSimulateDisruption }) {
  const { permission, isSupported, isReady, requestPermission, sendNotification } = useNotification()
  const [simulated, setSimulated] = useState(false)

  async function handleEnable() {
    const result = await requestPermission()
    if (result === 'granted') {
      console.log('[Demo] Notifications enabled. Check macOS System Settings > Notifications if they do not appear.')
    }
  }

  function handleSimulate() {
    const { situasjon } = disruptionData
    setSimulated(true)

    const sent = sendNotification(
      'Avvik på hjemreisen din',
      situasjon.oppsummering
    )

    if (!sent) {
      console.warn('[Demo] Notification not sent. Check: (1) browser permission, (2) macOS System Settings > Notifications > [browser]')
    }

    setTimeout(() => {
      onSimulateDisruption?.()
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
          <SecondaryButton onClick={handleSimulate} disabled={simulated} style={{ width: '100%' }}>
            {simulated ? 'Sender varsel...' : 'Simuler avvik'}
          </SecondaryButton>
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
