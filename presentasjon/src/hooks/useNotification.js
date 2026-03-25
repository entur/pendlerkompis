import { useState, useCallback, useEffect } from 'react'

/**
 * Hook for Web Notification API with PWA service worker support.
 * Uses ServiceWorkerRegistration.showNotification() — the correct API for PWAs.
 */
export default function useNotification() {
  const [permission, setPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'denied'
  )
  const [registration, setRegistration] = useState(null)

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((reg) => {
        setRegistration(reg)
        console.log('[Notification] Service worker ready:', reg)
      })
    }
  }, [])

  const requestPermission = useCallback(async () => {
    if (typeof Notification === 'undefined') return 'denied'
    const result = await Notification.requestPermission()
    setPermission(result)
    console.log('[Notification] Permission:', result)
    return result
  }, [])

  const sendNotification = useCallback((title, body) => {
    console.log('[Notification] Attempting to send:', { title, body, permission, hasRegistration: !!registration })

    if (permission !== 'granted') {
      console.warn('[Notification] Permission not granted:', permission)
      return false
    }

    if (registration) {
      registration.showNotification(title, {
        body,
        icon: '/icon.svg',
        tag: 'pendlerkompis-disruption',
      })
      console.log('[Notification] Sent via service worker')
      return true
    }

    // Fallback to Notification API (works in browser tabs, not installed PWAs)
    try {
      new Notification(title, { body, icon: '/icon.svg' })
      console.log('[Notification] Sent via Notification API fallback')
      return true
    } catch (e) {
      console.warn('[Notification] Both methods failed:', e)
      return false
    }
  }, [permission, registration])

  return {
    permission,
    isSupported: typeof Notification !== 'undefined',
    isReady: permission === 'granted' && !!registration,
    requestPermission,
    sendNotification,
  }
}
