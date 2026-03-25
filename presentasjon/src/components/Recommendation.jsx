import { PrimaryButton } from '@entur/button'
import { Paragraph } from '@entur/typography'

export default function Recommendation({ action, description, arrivalTime, onSelect }) {
  return (
    <div style={{
      border: '2px solid var(--colors-validation-mint, #1a8c5b)',
      borderRadius: '8px',
      padding: '1rem',
      marginTop: '0.75rem',
      backgroundColor: 'var(--colors-validation-mintContrast, #ebf7f0)',
    }}>
      <Paragraph>{description}</Paragraph>
      {arrivalTime && (
        <Paragraph style={{ fontWeight: 'bold', marginTop: '0.5rem' }}>
          Hjemme ca. {arrivalTime}
        </Paragraph>
      )}
      <div style={{ marginTop: '0.75rem' }}>
        <PrimaryButton onClick={onSelect}>
          Velg dette
        </PrimaryButton>
      </div>
    </div>
  )
}
