import { useEffect } from 'react'
import { useSidebarStore } from '@/stores/sidebar-store'

export function useSidebarShortcuts() {
  const { toggleAppSidebar, toggleIdeSidebar, toggleConnectorsPanel } = useSidebarStore()

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Ctrl (Windows/Linux) or Cmd (Mac)
      const isModifier = event.ctrlKey || event.metaKey

      // Ctrl+B or Cmd+B: Toggle AppSidebar
      if (isModifier && event.key === 'b' && !event.shiftKey) {
        event.preventDefault()
        toggleAppSidebar()
        return
      }

      // Ctrl+Shift+E or Cmd+Shift+E: Toggle IdeSidebar
      if (isModifier && event.shiftKey && event.key === 'E') {
        event.preventDefault()
        toggleIdeSidebar()
        return
      }

      // Ctrl+Shift+D or Cmd+Shift+D: Toggle ConnectorsPanel
      if (isModifier && event.shiftKey && event.key === 'D') {
        event.preventDefault()
        toggleConnectorsPanel()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [toggleAppSidebar, toggleIdeSidebar, toggleConnectorsPanel])
}
