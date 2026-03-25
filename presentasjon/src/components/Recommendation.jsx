import { PrimaryButton } from '@entur/button'
import { Paragraph } from '@entur/typography'

export default function Recommendation({ action, description, arrivalTime, travelLink, onSelect }) {
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
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginTop: '0.75rem' }}>
        <PrimaryButton onClick={onSelect}>
          Velg dette
        </PrimaryButton>
        {travelLink && (
          <a
            href={travelLink}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: 'var(--colors-brand-blue, #181c56)',
              fontSize: '0.9rem',
            }}
          >
            Se reise i Entur →
          </a>
        )}
      </div>
    </div>
  )
}
