import { useState, useCallback } from 'react'

const MOTOR_BASE_URL = 'http://localhost:8082'

/**
 * Hook for manually fetching recommendations from the motor API.
 * Returns the latest recommendation (Kontrakt B) if there is an active disruption.
 */
export default function useMotorApi() {
  const [recommendation, setRecommendation] = useState(null)
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const fetchRecommendation = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`${MOTOR_BASE_URL}/anbefaling?direction=fra_hjem&time=16:00`)
      if (!res.ok) throw new Error(`Motor API: ${res.status}`)
      const data = await res.json()

      if (data.type === 'avvik' && data.situasjon?.alvorlighet !== 'ingen') {
        setRecommendation(data)
      } else {
        setRecommendation(null)
      }
      setError(null)
    } catch (e) {
      console.warn('[Motor API] Fetch failed:', e.message)
      setError(e.message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const stopPolling = useCallback(() => {}, [])
  const startPolling = useCallback(() => {}, [])

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
    isLoading,
    refresh: fetchRecommendation,
    stopPolling,
    startPolling,
    sendFeedback,
  }
}
