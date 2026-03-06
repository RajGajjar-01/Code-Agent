import { Layers, Plus, MessageSquare, Trash2, Plug } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useChatStore } from '@/stores/chat-store'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useEffect } from 'react'
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuAction,
} from '@/components/ui/sidebar'

export function AppSidebar() {
    const { toggleConnectorsPanel, connectorsPanelOpen } = useSidebarStore()
    const {
        conversations,
        conversationId,
        loadConversations,
        openConversation,
        deleteConversation,
        startNewChat,
    } = useChatStore()

    useEffect(() => {
        loadConversations()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const handleConversationClick = async (id: string) => {
        await openConversation(id)
    }

    return (
        <Sidebar collapsible="offcanvas">
            <SidebarHeader className="border-b border-sidebar-border h-[60px] p-0">
                <div className="flex items-center gap-2.5 px-5 h-full">
                    <div className="flex items-center justify-center h-8 w-8 shrink-0">
                        <Layers className="h-7 w-7 text-black" strokeWidth={2.5} />
                    </div>
                    <span className="text-lg font-bold text-black tracking-tight whitespace-nowrap flex-1">
                        WP Agent
                    </span>
                </div>
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup className="px-0">
                    <div className="px-2 pb-2">
                        <Button
                            onClick={startNewChat}
                            className="w-full justify-center gap-2 bg-primary hover:bg-primary/90 text-black font-medium rounded-lg h-11"
                        >
                            <Plus className="h-5 w-5" strokeWidth={2.5} />
                            New Chat
                        </Button>
                    </div>
                </SidebarGroup>

                <SidebarGroup className="px-0">
                    <SidebarGroupLabel className="px-2">Recent</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {conversations.length === 0 ? (
                                <div className="px-2 py-6 text-center">
                                    <p className="text-sm text-muted-foreground">No conversations yet</p>
                                </div>
                            ) : (
                                conversations.map((convo) => (
                                    <SidebarMenuItem key={convo.id}>
                                        <SidebarMenuButton
                                            onClick={() => handleConversationClick(convo.id)}
                                            isActive={convo.id === conversationId}
                                        >
                                            <MessageSquare className="h-4 w-4" strokeWidth={2} />
                                            <span>{convo.title}</span>
                                        </SidebarMenuButton>
                                        <SidebarMenuAction
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                deleteConversation(convo.id)
                                            }}
                                            showOnHover
                                        >
                                            <Trash2 className="h-3.5 w-3.5" strokeWidth={2} />
                                            <span className="sr-only">Delete conversation</span>
                                        </SidebarMenuAction>
                                    </SidebarMenuItem>
                                ))
                            )}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>

            <SidebarFooter className="border-t border-sidebar-border bg-sidebar-accent/50 p-0">
                <SidebarGroup className="p-0 pt-2">
                    <SidebarGroupLabel className="px-2">Tools</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <div className="flex flex-col gap-2 px-2 pb-2">
                            <Button
                                variant="ghost"
                                onClick={toggleConnectorsPanel}
                                className="w-full justify-start gap-2.5 h-9 px-3 hover:bg-sidebar-accent text-black font-medium"
                            >
                                <Plug className="h-4 w-4" strokeWidth={2} />
                                <span>Connectors</span>
                                {connectorsPanelOpen && (
                                    <span className="ml-auto h-2 w-2 rounded-full bg-green-500 shrink-0" />
                                )}
                            </Button>
                        </div>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarFooter>
        </Sidebar>
    )
}
