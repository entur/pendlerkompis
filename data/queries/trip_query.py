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
          date
        }
        toEstimatedCall {
          aimedArrivalTime
          expectedArrivalTime
          cancellation
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


def trip_variables(
    from_coords: tuple[float, float],
    to_coords: tuple[float, float],
    date_time: str,
    num_patterns: int = 5,
) -> dict:
    """Build GraphQL variables for the trip query."""
    return {
        "from": {
            "coordinates": {
                "latitude": from_coords[0],
                "longitude": from_coords[1],
            }
        },
        "to": {
            "coordinates": {
                "latitude": to_coords[0],
                "longitude": to_coords[1],
            }
        },
        "dateTime": date_time,
        "numTripPatterns": num_patterns,
    }
