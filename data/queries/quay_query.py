"""GraphQL query for quay departure boards (destination stop live data)."""

QUAY_DEPARTURES_QUERY = """
query QuayDepartures($id: String!, $numberOfDepartures: Int!, $timeRange: Int) {
  quay(id: $id) {
    id
    name
    estimatedCalls(
      numberOfDepartures: $numberOfDepartures,
      timeRange: $timeRange
    ) {
      aimedArrivalTime
      expectedArrivalTime
      aimedDepartureTime
      expectedDepartureTime
      cancellation
      date
      serviceJourney {
        id
        line {
          id
          publicCode
          name
          transportMode
        }
      }
    }
  }
}
"""


def quay_variables(quay_id: str, num_departures: int = 20, time_range: int = 7200) -> dict:
    return {
        "id": quay_id,
        "numberOfDepartures": num_departures,
        "timeRange": time_range,
    }
