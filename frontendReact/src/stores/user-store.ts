import { create } from 'zustand'
import { userApi, setAccessToken } from '@/lib/axios'

interface UserState {
    id: number | null
    email: string
    name: string
    isAuthenticated: boolean
    isLoading: boolean

    checkSession: () => Promise<void>
    login: (email: string, password: string) => Promise<void>
    register: (email: string, name: string, password: string) => Promise<void>
    logout: () => Promise<void>
}

export const useUserStore = create<UserState>((set) => ({
    id: null,
    email: '',
    name: '',
    isAuthenticated: false,
    isLoading: true,

    checkSession: async () => {
        set({ isLoading: true })
        try {
            const { data } = await userApi.getMe()
            set({
                id: data.id,
                email: data.email,
                name: data.name,
                isAuthenticated: true,
                isLoading: false,
            })
        } catch {
            set({ id: null, email: '', name: '', isAuthenticated: false, isLoading: false })
        }
    },

    login: async (email, password) => {
        const { data } = await userApi.login(email, password)
        setAccessToken(data.access_token)
        
        const userResponse = await userApi.getMe()
        set({
            id: userResponse.data.id,
            email: userResponse.data.email,
            name: userResponse.data.name,
            isAuthenticated: true
        })
    },

    register: async (email, name, password) => {
        const { data } = await userApi.register(email, name, password)
        setAccessToken(data.access_token)
        
        const userResponse = await userApi.getMe()
        set({
            id: userResponse.data.id,
            email: userResponse.data.email,
            name: userResponse.data.name,
            isAuthenticated: true
        })
    },

    logout: async () => {
        await userApi.logout()
        setAccessToken(null)
        set({ id: null, email: '', name: '', isAuthenticated: false })
    },
}))
