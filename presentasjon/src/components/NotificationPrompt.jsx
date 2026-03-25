import { PrimaryButton, SecondaryButton } from '@entur/button'
import { Paragraph } from '@entur/typography'
import { SmallAlertBox } from '@entur/alert'
import useNotification from '../hooks/useNotification.js'
import disruptionData from '../mock/disruption.json'

export default function NotificationPrompt({ onSimulateDisruption }) {
  const { permission, isSupported, requestPermission, sendNotification } = useNotification()

  async function handleEnable() {
    await requestPermission()
  }

  function handleSimulate() {
    const { situasjon } = disruptionData

    sendNotification(
      'Avvik på hjemreisen din',
      situasjon.oppsummering
    )

    // Show the disruption alert in the app after a short delay
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
          <SecondaryButton onClick={handleSimulate} style={{ width: '100%' }}>
            Simuler avvik
          </SecondaryButton>
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
