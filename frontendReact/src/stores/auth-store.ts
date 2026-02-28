import { create } from 'zustand'
import { authApi, driveApi } from '@/lib/axios'
import type { Breadcrumb, DriveItem } from '@/types'

interface AuthStore {
    isConnected: boolean
    userEmail: string
    userName: string
    userPicture: string
    breadcrumbs: Breadcrumb[]
    driveItems: DriveItem[]
    isDriveLoading: boolean

    checkAuthStatus: () => Promise<void>
    disconnect: () => Promise<void>
    loadFolder: (folderId: string) => Promise<void>
    navigateToBreadcrumb: (index: number) => void
}

export const useAuthStore = create<AuthStore>((set, get) => ({
    isConnected: false,
    userEmail: '',
    userName: '',
    userPicture: '',
    breadcrumbs: [{ id: 'root', name: 'My Drive' }],
    driveItems: [],
    isDriveLoading: false,

    checkAuthStatus: async () => {
        try {
            const { data } = await authApi.getStatus()
            if (data.connected) {
                set({
                    isConnected: true,
                    userEmail: data.email || '',
                    userName: data.name || 'Google User',
                    userPicture: data.picture || '',
                    breadcrumbs: [{ id: 'root', name: 'My Drive' }],
                })
                get().loadFolder('root')
            } else {
                set({ isConnected: false, userEmail: '', userName: '', userPicture: '' })
            }
        } catch (e) {
            console.error('Auth status check failed:', e)
        }
    },

    disconnect: async () => {
        try {
            await authApi.disconnect()
            set({
                isConnected: false,
                userEmail: '',
                userName: '',
                userPicture: '',
                driveItems: [],
                breadcrumbs: [{ id: 'root', name: 'My Drive' }],
            })
        } catch (e) {
            console.error('Disconnect failed:', e)
        }
    },

    loadFolder: async (folderId) => {
        set({ isDriveLoading: true })
        try {
            const { data } = await driveApi.listFolder(folderId)
            set({ driveItems: data.items, isDriveLoading: false })
        } catch (e) {
            console.error('Failed to load Drive folder:', e)
            set({ driveItems: [], isDriveLoading: false })
        }
    },

    navigateToBreadcrumb: (index) => {
        const { breadcrumbs } = get()
        if (index === breadcrumbs.length - 1) return
        const newBreadcrumbs = breadcrumbs.slice(0, index + 1)
        set({ breadcrumbs: newBreadcrumbs })
        get().loadFolder(newBreadcrumbs[index].id)
    },
}))
