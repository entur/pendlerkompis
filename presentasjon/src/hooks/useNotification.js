import { useState, useCallback } from 'react'

/**
 * Hook for Web Notification API.
 * Forberedt for senere bruk når Motor leverer push-events.
 */
export default function useNotification() {
  const [permission, setPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'denied'
  )

  const requestPermission = useCallback(async () => {
    if (typeof Notification === 'undefined') return 'denied'
    const result = await Notification.requestPermission()
    setPermission(result)
    return result
  }, [])

  const sendNotification = useCallback((title, body) => {
    if (permission !== 'granted') {
      console.log('Notification ikke tillatt. Ville vist:', { title, body })
      return null
    }
    return new Notification(title, { body, icon: '/pendlerkompis-icon.png' })
  }, [permission])

  return {
    permission,
    isSupported: typeof Notification !== 'undefined',
    requestPermission,
    sendNotification,
  }
}
