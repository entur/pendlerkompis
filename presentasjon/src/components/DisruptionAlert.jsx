import { BannerAlertBox } from '@entur/alert'
import { Heading4, Paragraph } from '@entur/typography'
import Recommendation from './Recommendation.jsx'
import Alternative from './Alternative.jsx'

function formatTime(isoString) {
  if (!isoString) return null
  const date = new Date(isoString)
  return date.toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })
}

export default function DisruptionAlert({ data, onSelect }) {
  const { situasjon, anbefaling, andre_alternativer } = data

  const variant = situasjon.alvorlighet === 'hoy' || situasjon.alvorlighet === 'høy'
    ? 'negative'
    : situasjon.alvorlighet === 'middels'
      ? 'warning'
      : 'info'

  return (
    <div>
      <BannerAlertBox
        variant={variant}
        title="Avvik på hjemreisen din"
      >
        <Paragraph>{situasjon.oppsummering}</Paragraph>
      </BannerAlertBox>

      <div style={{ marginTop: '1.5rem' }}>
        <Heading4>Anbefaling</Heading4>
        <Recommendation
          action={anbefaling.handling}
          description={anbefaling.beskrivelse}
          arrivalTime={formatTime(anbefaling.estimert_ankomst_hjem)}
          onSelect={() => onSelect(anbefaling.handling, anbefaling.beskrivelse)}
        />
      </div>

      {andre_alternativer.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <Heading4>Andre alternativer</Heading4>
          {andre_alternativer.map((alt, i) => (
            <Alternative
              key={i}
              action={alt.handling}
              description={alt.beskrivelse}
              arrivalTime={formatTime(alt.estimert_ankomst_hjem)}
              onSelect={() => onSelect(alt.handling, alt.beskrivelse)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
