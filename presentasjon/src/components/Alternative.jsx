import { SecondaryButton } from '@entur/button'
import { Paragraph } from '@entur/typography'

export default function Alternative({ action, description, arrivalTime, onSelect }) {
  return (
    <div style={{
      border: '1px solid var(--colors-greys-grey20, #ddd)',
      borderRadius: '8px',
      padding: '1rem',
      marginTop: '0.75rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '1rem',
    }}>
      <div>
        <Paragraph margin="none">{description}</Paragraph>
        {arrivalTime && (
          <Paragraph margin="none" style={{ fontWeight: 'bold', marginTop: '0.25rem' }}>
            Hjemme ca. {arrivalTime}
          </Paragraph>
        )}
      </div>
      <SecondaryButton onClick={onSelect} size="small">
        Velg
      </SecondaryButton>
    </div>
  )
}
