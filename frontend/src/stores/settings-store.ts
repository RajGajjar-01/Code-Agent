import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type LLMProvider = 'groq' | 'glm5' | 'gemini'

interface SettingsStore {
    llmProvider: LLMProvider
    setLLMProvider: (provider: LLMProvider) => void
    wpCliWpPath: string
    setWpCliWpPath: (path: string) => void
    wpCliDefaultUrl: string
    setWpCliDefaultUrl: (url: string) => void
}

export const useSettingsStore = create<SettingsStore>()(
    persist(
        (set) => ({
            llmProvider: 'groq',
            setLLMProvider: (provider) => set({ llmProvider: provider }),
            wpCliWpPath: '',
            setWpCliWpPath: (path) => set({ wpCliWpPath: path }),
            wpCliDefaultUrl: '',
            setWpCliDefaultUrl: (url) => set({ wpCliDefaultUrl: url }),
        }),
        {
            name: 'wp-agent-settings',
        }
    )
)
