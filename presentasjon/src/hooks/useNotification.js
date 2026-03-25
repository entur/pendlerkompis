import { useState, useCallback, useEffect } from 'react'

/**
 * Hook for Web Notification API with PWA service worker support.
 * Uses service worker notifications when available, falls back to Notification API.
 */
export default function useNotification() {
  const [permission, setPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'denied'
  )
  const [registration, setRegistration] = useState(null)

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(setRegistration)
    }
  }, [])

  const requestPermission = useCallback(async () => {
    if (typeof Notification === 'undefined') return 'denied'
    const result = await Notification.requestPermission()
    setPermission(result)
    return result
  }, [])

  const sendNotification = useCallback((title, body) => {
    if (permission !== 'granted') {
      console.log('Notification not permitted. Would show:', { title, body })
      return null
    }

    // Prefer service worker notifications (works when app is in background)
    if (registration) {
      registration.showNotification(title, {
        body,
        icon: '/icon-192.png',
        badge: '/icon-192.png',
      })
      return null
    }

    return new Notification(title, { body })
  }, [permission, registration])

  return {
    permission,
    isSupported: typeof Notification !== 'undefined',
    requestPermission,
    sendNotification,
  }
}
