import axios from 'axios'
import type {
    AuthStatus,
    ChatResponse,
    DriveResponse,
    AttachmentRef,
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
            // Skip refresh for auth endpoints to prevent infinite loops
            const authEndpoints = ['/api/auth/login', '/api/auth/register', '/api/auth/refresh', '/api/auth/me']
            if (authEndpoints.some(endpoint => originalRequest.url?.includes(endpoint))) {
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
                // Only redirect if not already on a public route
                const publicRoutes = ['/login', '/signup']
                const isPublicRoute = publicRoutes.some(route => window.location.pathname.includes(route))

                if (!isPublicRoute) {
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
    uploadAttachments(files: File[]) {
        const formData = new FormData()
        files.forEach((f) => formData.append('files', f))
        return api.post<AttachmentRef[]>('/api/chat/attachments', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },

    send(
        message: string,
        conversationId: string | null,
        userEmail: string,
        llmProvider?: string,
        attachments?: AttachmentRef[],
    ) {
        if (!userEmail) {
            throw new Error('Authentication required. Please log in to send messages.')
        }
        return api.post<ChatResponse>('/api/chat', {
            message,
            conversation_id: conversationId,
            user_email: userEmail,
            llm_provider: llmProvider,
            attachments,
        })
    },

    listConversations(userEmail: string, limit = 40) {
        if (!userEmail) {
            throw new Error('Authentication required. Please log in to view conversations.')
        }
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

    refresh() {
        return api.post<{ access_token: string; token_type: string }>('/api/auth/refresh')
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

