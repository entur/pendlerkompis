export default function Alternative({ action, description, arrivalTime, travelLink, onSelect }) {
  return (
    <div
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
      style={{
        border: '1px solid #ccc',
        borderRadius: '8px',
        padding: '1rem',
        marginTop: '0.75rem',
        cursor: 'pointer',
        background: 'white',
      }}
    >
      <p style={{ margin: 0, fontSize: '1rem', lineHeight: 1.4 }}>{description}</p>
      {arrivalTime && (
        <p style={{ margin: '0.25rem 0 0', fontWeight: 'bold', fontSize: '1rem' }}>
          Hjemme ca. {arrivalTime}
        </p>
      )}
      {travelLink && (
        <a
          href={travelLink}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          style={{
            display: 'inline-block',
            marginTop: '0.5rem',
            color: 'var(--colors-brand-blue, #181c56)',
            fontSize: '0.9rem',
          }}
        >
          Se reise i Entur →
        </a>
      )}
    </div>
  )
}
