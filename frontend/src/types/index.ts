export interface Message {
    role: 'user' | 'assistant'
    content: string
    tool_calls?: ToolCallGroup
    attachments?: AttachmentRef[]
}

export interface AttachmentRef {
    id: string
    filename: string
    content_type: string
    size_bytes: number
    url: string
    local_path: string
}

export interface ToolCallGroup {
    calls: ToolCall[]
}

export interface ToolCall {
    name: string
    function?: string
    status: 'success' | 'error' | 'pending'
    arguments: Record<string, unknown>
    result?: unknown
}

export interface Conversation {
    id: string
    title: string
    created_at?: string
}

export interface DriveItem {
    id: string
    name: string
    mime_type: string
    modified_time?: string
}

export interface Breadcrumb {
    id: string
    name: string
}


export interface ChatResponse {
    response: string
    conversation_id: string
    tool_calls?: ToolCall[]
}

export interface AuthStatus {
    connected: boolean
    email?: string
    name?: string
    picture?: string
}

export interface DriveResponse {
    items: DriveItem[]
    next_page_token?: string
}

export interface WordPressSite {
    id: number
    name?: string | null
    base_url: string
    username: string
    created_at?: string
    updated_at?: string
}
