import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type LLMProvider = 'groq' | 'glm5' | 'gemini'

interface SettingsStore {
    llmProvider: LLMProvider
    setLLMProvider: (provider: LLMProvider) => void
}

export const useSettingsStore = create<SettingsStore>()(
    persist(
        (set) => ({
            llmProvider: 'groq',
            setLLMProvider: (provider) => set({ llmProvider: provider }),
        }),
        {
            name: 'wp-agent-settings',
        }
    )
)
