"""GraphQL query strings for the Entur Journey Planner v3 API."""

TRIP_QUERY = """
query PendlerTrip(
  $from: Location!,
  $to: Location!,
  $dateTime: DateTime!,
  $numTripPatterns: Int
) {
  trip(
    from: $from,
    to: $to,
    dateTime: $dateTime,
    numTripPatterns: $numTripPatterns,
    includeRealtimeCancellations: true,
    modes: {
      accessMode: foot,
      egressMode: foot,
      transportModes: [
        { transportMode: rail },
        { transportMode: bus },
        { transportMode: tram },
        { transportMode: metro },
        { transportMode: water }
      ]
    }
  ) {
    tripPatterns {
      expectedStartTime
      expectedEndTime
      duration
      legs {
        mode
        duration
        fromPlace {
          name
          quay {
            id
            name
            stopPlace { id name }
          }
        }
        toPlace {
          name
          quay {
            id
            name
            stopPlace { id name }
          }
        }
        fromEstimatedCall {
          aimedDepartureTime
          expectedDepartureTime
          cancellation
          realtimeState
          date
        }
        toEstimatedCall {
          aimedArrivalTime
          expectedArrivalTime
          cancellation
          realtimeState
          date
        }
        line {
          id
          publicCode
          name
          transportMode
        }
        serviceJourney {
          id
        }
        situations {
          id
          situationNumber
          summary { value }
          description { value }
          severity
          reportType
          validityPeriod {
            startTime
            endTime
          }
        }
      }
    }
  }
}
"""


def _location(coords: tuple[float, float], place_id: str | None = None) -> dict:
    """Build a Location input — prefers stop place ID over coordinates."""
    if place_id:
        return {"place": place_id}
    return {"coordinates": {"latitude": coords[0], "longitude": coords[1]}}


def trip_variables(
    from_coords: tuple[float, float],
    to_coords: tuple[float, float],
    date_time: str,
    num_patterns: int = 5,
    from_place: str | None = None,
    to_place: str | None = None,
) -> dict:
    """Build GraphQL variables for the trip query."""
    return {
        "from": _location(from_coords, from_place),
        "to": _location(to_coords, to_place),
        "dateTime": date_time,
        "numTripPatterns": num_patterns,
    }
