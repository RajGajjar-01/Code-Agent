import { create } from 'zustand'

interface SidebarState {
  // State
  appSidebarOpen: boolean
  ideSidebarOpen: boolean
  connectorsPanelOpen: boolean
  
  // Actions
  toggleAppSidebar: () => void
  toggleIdeSidebar: () => void
  toggleConnectorsPanel: () => void
  setAppSidebarOpen: (open: boolean) => void
  setIdeSidebarOpen: (open: boolean) => void
  setConnectorsPanelOpen: (open: boolean) => void
}

// Storage key
const STORAGE_KEY = 'sidebar-state'

// Debounce timer
let saveTimer: NodeJS.Timeout | null = null

// Load initial state from localStorage
const loadState = (): Pick<SidebarState, 'appSidebarOpen' | 'ideSidebarOpen' | 'connectorsPanelOpen'> => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return {
        appSidebarOpen: parsed.appSidebarOpen ?? true,
        ideSidebarOpen: parsed.ideSidebarOpen ?? true,
        connectorsPanelOpen: parsed.connectorsPanelOpen ?? true,
      }
    }
  } catch (error) {
    console.warn('Failed to load sidebar state from localStorage:', error)
  }
  
  // Default state
  return {
    appSidebarOpen: true,
    ideSidebarOpen: true,
    connectorsPanelOpen: true,
  }
}

// Save state to localStorage with debouncing (300ms)
const saveState = (state: Pick<SidebarState, 'appSidebarOpen' | 'ideSidebarOpen' | 'connectorsPanelOpen'>) => {
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
  
  saveTimer = setTimeout(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch (error) {
      console.warn('Failed to save sidebar state to localStorage:', error)
    }
  }, 300)
}

export const useSidebarStore = create<SidebarState>((set, get) => ({
  // Initialize with loaded state
  ...loadState(),
  
  toggleAppSidebar: () => {
    set((state) => {
      const newState = { ...state, appSidebarOpen: !state.appSidebarOpen }
      saveState(newState)
      return newState
    })
  },
  
  toggleIdeSidebar: () => {
    set((state) => {
      const newState = { ...state, ideSidebarOpen: !state.ideSidebarOpen }
      saveState(newState)
      return newState
    })
  },
  
  toggleConnectorsPanel: () => {
    set((state) => {
      const newState = { ...state, connectorsPanelOpen: !state.connectorsPanelOpen }
      saveState(newState)
      return newState
    })
  },
  
  setAppSidebarOpen: (open: boolean) => {
    set((state) => {
      const newState = { ...state, appSidebarOpen: open }
      saveState(newState)
      return newState
    })
  },
  
  setIdeSidebarOpen: (open: boolean) => {
    set((state) => {
      const newState = { ...state, ideSidebarOpen: open }
      saveState(newState)
      return newState
    })
  },
  
  setConnectorsPanelOpen: (open: boolean) => {
    set((state) => {
      const newState = { ...state, connectorsPanelOpen: open }
      saveState(newState)
      return newState
    })
  },
}))
