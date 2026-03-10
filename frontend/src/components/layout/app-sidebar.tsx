import { Plus, MessageSquare, Trash2, Plug, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useChatStore } from '@/stores/chat-store'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useEffect } from 'react'
import { Link } from 'react-router'
import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuAction,
    SidebarTrigger,
    SidebarFooter,
    useSidebar,
} from '@/components/ui/sidebar'

export function AppSidebar() {
    const { toggleConnectorsPanel, connectorsPanelOpen } = useSidebarStore()
    const { state, isMobile } = useSidebar()
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
        <Sidebar collapsible="icon">
            <SidebarHeader className="border-sidebar-border h-[60px] p-0 flex flex-row items-center justify-between px-4 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0 transition-all duration-200 gap-0 shrink-0">
                <div className="flex items-center group-data-[collapsible=icon]:hidden">
                    <span className="text-sm tracking-wider leading-none uppercase font-medium text-foreground">Agent</span>
                </div>
                <SidebarTrigger />
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup className="px-0">
                    <div className="px-2 flex flex-col gap-2 pb-2">
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="ghost"
                                    onClick={toggleConnectorsPanel}
                                    className="w-full justify-start gap-2.5 h-9 px-3 hover:bg-sidebar-accent text-black font-medium group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0"
                                >
                                    <Plug className="h-4 w-4" strokeWidth={2} />
                                    <span className="group-data-[collapsible=icon]:hidden">Connectors</span>
                                    {connectorsPanelOpen && (
                                        <span className="ml-auto h-2 w-2 rounded-full bg-green-500 shrink-0 group-data-[collapsible=icon]:hidden" />
                                    )}
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent side="right" align="center" hidden={state !== 'collapsed' || isMobile}>
                                Connectors
                            </TooltipContent>
                        </Tooltip>

                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    onClick={startNewChat}
                                    className="w-full justify-center gap-2 bg-primary hover:bg-primary/90 text-black font-medium rounded-lg group-data-[collapsible=icon]:rounded-xl h-10 group-data-[collapsible=icon]:px-0"
                                >
                                    <Plus className="h-5 w-5" strokeWidth={2.5} />
                                    <span className="group-data-[collapsible=icon]:hidden">New Chat</span>
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent side="right" align="center" hidden={state !== 'collapsed' || isMobile}>
                                New Chat
                            </TooltipContent>
                        </Tooltip>
                    </div>
                </SidebarGroup>

                <SidebarGroup className="px-0 group-data-[collapsible=icon]:hidden">
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
                                            tooltip={convo.title}
                                        >
                                            <MessageSquare className="h-4 w-4" strokeWidth={2} />
                                            <span className="group-data-[collapsible=icon]:hidden">{convo.title}</span>
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

            <SidebarFooter className="px-2 group-data-[collapsible=icon]:px-0">
                <SidebarMenu>
                    <SidebarMenuItem className="flex justify-start group-data-[collapsible=icon]:justify-center">
                        <SidebarMenuButton asChild tooltip="Profile" className="group-data-[collapsible=icon]:justify-center">
                            <Link to="/profile">
                                <div className="flex items-center justify-center h-7 w-7 rounded-full bg-muted shrink-0">
                                    <User className="h-3.5 w-3.5 text-muted-foreground" strokeWidth={2.5} />
                                </div>
                                <span className="group-data-[collapsible=icon]:hidden">Profile</span>
                            </Link>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarFooter>
        </Sidebar>
    )
}
