import axios from 'axios'
import type {
    AuthStatus,
    ChatResponse,
    DriveResponse,
    FileResponse,
    RootsResponse,
    TreeResponse,
} from '@/types'

const api = axios.create({
    baseURL: '',
    headers: { 'Content-Type': 'application/json' },
    withCredentials: true,
})

let accessToken: string | null = null

export const setAccessToken = (token: string | null) => {
    accessToken = token
}

export const getAccessToken = () => accessToken

api.interceptors.request.use(
    (config) => {
        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
            if (originalRequest.url?.includes('/api/auth/login') || 
                originalRequest.url?.includes('/api/auth/register') ||
                originalRequest.url?.includes('/api/auth/refresh')) {
                return Promise.reject(error)
            }

            originalRequest._retry = true

            try {
                const { data } = await axios.post(
                    '/api/auth/refresh',
                    {},
                    { withCredentials: true }
                )

                setAccessToken(data.access_token)
                originalRequest.headers.Authorization = `Bearer ${data.access_token}`

                return api(originalRequest)
            } catch (refreshError) {
                setAccessToken(null)
                if (!window.location.pathname.includes('/login') && 
                    !window.location.pathname.includes('/signup')) {
                    window.location.href = '/login'
                }
                return Promise.reject(refreshError)
            }
        }

        return Promise.reject(error)
    }
)

// Chat
export const chatApi = {
    send(message: string, conversationId: string | null, userEmail: string) {
        return api.post<ChatResponse>('/api/chat', {
            message,
            conversation_id: conversationId,
            user_email: userEmail,
        })
    },

    listConversations(userEmail: string, limit = 40) {
        return api.get<{ id: string; title: string }[]>('/api/conversations', {
            params: { user_email: userEmail, limit },
        })
    },

    getConversation(id: string) {
        return api.get<{ messages: { role: string; content: string; tool_calls?: unknown }[] }>(
            `/api/conversations/${id}`,
        )
    },

    deleteConversation(id: string) {
        return api.delete(`/api/conversations/${id}`)
    },
}

// Auth (register/login/logout/me)
export const userApi = {
    register(email: string, name: string, password: string) {
        return api.post<{ access_token: string; token_type: string }>(
            '/api/auth/register',
            { email, name, password },
        )
    },

    login(email: string, password: string) {
        return api.post<{ access_token: string; token_type: string }>(
            '/api/auth/login',
            { email, password },
        )
    },

    logout() {
        return api.post('/api/auth/logout')
    },

    getMe() {
        return api.get<{ id: number; email: string; name: string; is_active: boolean }>('/api/auth/me')
    },
}

// Google Drive Auth
export const authApi = {
    getStatus() {
        return api.get<AuthStatus>('/api/auth/status')
    },

    disconnect() {
        return api.post('/api/auth/disconnect')
    },

    getLoginUrl() {
        return '/api/auth/google/login'
    },
}

export const driveApi = {
    listFolder(parentId = 'root', pageToken?: string | null) {
        return api.get<DriveResponse>('/api/drive/folders', {
            params: { parent_id: parentId, ...(pageToken ? { page_token: pageToken } : {}) },
        })
    },
}

// IDE Filesystem
export const ideApi = {
    getRoots() {
        return api.get<RootsResponse>('/api/ide/tree/roots')
    },

    getTree(dir: string) {
        return api.get<TreeResponse>('/api/ide/tree', { params: { dir } })
    },

    readFile(path: string) {
        return api.get<FileResponse>('/api/ide/file', { params: { path } })
    },

    writeFile(path: string, content: string) {
        return api.post('/api/ide/file', { path, content })
    },

    createNode(parentPath: string, name: string, type: string) {
        return api.post('/api/ide/create', { parent_path: parentPath, name, type })
    },
}
