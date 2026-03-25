import { useState, useEffect, useCallback, useRef } from 'react'

const MOTOR_BASE_URL = 'http://localhost:8082'
const POLL_INTERVAL_MS = 10_000

/**
 * Hook that polls the motor API for recommendations every 10 seconds.
 * Returns the latest recommendation (Kontrakt B) if there is an active disruption.
 */
export default function useMotorApi() {
  const [recommendation, setRecommendation] = useState(null)
  const [error, setError] = useState(null)
  const [isPolling, setIsPolling] = useState(true)
  const intervalRef = useRef(null)

  const fetchRecommendation = useCallback(async () => {
    try {
      const res = await fetch(`${MOTOR_BASE_URL}/anbefaling?direction=fra_jobb`)
      if (!res.ok) throw new Error(`Motor API: ${res.status}`)
      const data = await res.json()

      // Only update if there is an active disruption
      if (data.type === 'avvik' && data.situasjon?.alvorlighet !== 'ingen') {
        setRecommendation(data)
      } else {
        setRecommendation(null)
      }
      setError(null)
    } catch (e) {
      console.warn('[Motor API] Polling failed:', e.message)
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    if (!isPolling) return

    fetchRecommendation()
    intervalRef.current = setInterval(fetchRecommendation, POLL_INTERVAL_MS)

    return () => clearInterval(intervalRef.current)
  }, [isPolling, fetchRecommendation])

  const stopPolling = useCallback(() => {
    setIsPolling(false)
    clearInterval(intervalRef.current)
  }, [])

  const startPolling = useCallback(() => {
    setIsPolling(true)
  }, [])

  const sendFeedback = useCallback(async (action, alternativId) => {
    try {
      await fetch(`${MOTOR_BASE_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bruker_id: 'rolf-1',
          valgt_handling: action,
          alternativ_id: alternativId || null,
        }),
      })
      console.log('[Motor API] Feedback sent:', action)
    } catch (e) {
      console.warn('[Motor API] Feedback failed:', e.message)
    }
  }, [])

  return {
    recommendation,
    error,
    isPolling,
    stopPolling,
    startPolling,
    sendFeedback,
  }
}
