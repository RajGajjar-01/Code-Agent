import { useEffect } from 'react'
import { LogOut, FolderOpen, Loader2, ChevronRight, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { DriveFileList } from '@/components/drive/drive-file-list'
import { useAuthStore } from '@/stores/auth-store'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useChatStore } from '@/stores/chat-store'
import { authApi } from '@/lib/axios'
import { cn } from '@/lib/utils'
import driveLogo from '@/assets/google-drive.svg'

export function ConnectorsPanel() {
    const {
        isConnected,
        userEmail,
        userName,
        userPicture,
        breadcrumbs,
        driveItems,
        isDriveLoading,
        checkAuthStatus,
        disconnect,
        loadFolder,
        navigateToBreadcrumb,
    } = useAuthStore()

    const { connectorsPanelOpen, toggleConnectorsPanel } = useSidebarStore()
    const { setUserEmail, loadConversations } = useChatStore()

    useEffect(() => {
        checkAuthStatus()
        const params = new URLSearchParams(window.location.search)
        if (params.get('google_auth') === 'success') {
            window.history.replaceState({}, document.title, window.location.pathname)
            checkAuthStatus()
        }
    }, [checkAuthStatus])

    useEffect(() => {
        if (isConnected && userEmail) {
            setUserEmail(userEmail)
            loadConversations()
        }
    }, [isConnected, userEmail, setUserEmail, loadConversations])

    const handleFolderClick = (id: string, name: string) => {
        useAuthStore.setState((s) => ({
            breadcrumbs: [...s.breadcrumbs, { id, name }],
        }))
        loadFolder(id)
    }

    if (!connectorsPanelOpen) return null

    return (
        <aside className="w-[300px] min-w-[300px] max-w-[300px] bg-sidebar border-l border-sidebar-border flex flex-col shrink-0 h-full overflow-hidden z-[100]" role="complementary" aria-label="Connectors sidebar">
            {/* Header */}
            <div className="flex items-center justify-between h-[60px] px-5 border-b border-sidebar-border bg-sidebar shrink-0">
                <h3 className="text-[0.95rem] font-bold truncate text-sidebar-foreground">Connectors</h3>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleConnectorsPanel}
                    className="h-6 w-6 hover:bg-sidebar-accent"
                    aria-label="Close connectors panel"
                    aria-expanded={connectorsPanelOpen}
                    aria-controls="connectors-panel-content"
                >
                    <X className="h-4 w-4" />
                </Button>
            </div>

            <ScrollArea className="flex-1 w-full" id="connectors-panel-content" role="region" aria-label="Connectors panel content">
                <div className="p-4 space-y-4 min-w-0">
                    {/* Google Drive Card */}
                    <div className="bg-background border border-sidebar-border rounded-2xl p-4 shadow-sm transition-all hover:border-primary/50 group overflow-hidden">
                        <div className="flex justify-between items-start gap-2 mb-4">
                            <div className="flex-1 min-w-0 text-left">
                                <h4 className="text-[0.9rem] font-bold text-foreground truncate">Google Drive</h4>
                                <p className="text-[0.75rem] text-muted-foreground mt-0.5 break-words">
                                    {isConnected ? 'Account connected successfully.' : 'Connect and access your files.'}
                                </p>
                            </div>
                            <div className="w-11 h-11 flex items-center justify-center bg-secondary rounded-xl shrink-0 group-hover:bg-background group-hover:shadow-sm transition-all">
                                <img src={driveLogo} alt="Google Drive" className="w-8 h-8" />
                            </div>
                        </div>

                        <div className="flex gap-2 w-full">
                            {!isConnected ? (
                                <Button
                                    className="flex-1 h-9 rounded-lg text-[0.8rem] font-bold truncate"
                                    onClick={() => (window.location.href = authApi.getLoginUrl())}
                                >
                                    Connect
                                </Button>
                            ) : (
                                <>
                                    <Button
                                        variant="outline"
                                        className="flex-1 h-9 rounded-lg border-primary text-primary bg-primary/5 hover:bg-primary hover:text-white text-[0.8rem] font-bold gap-2 min-w-0 px-2"
                                        onClick={() => loadFolder('root')}
                                    >
                                        <FolderOpen className="w-4 h-4 shrink-0" />
                                        <span className="truncate">Browse Files</span>
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={disconnect}
                                        className="h-9 w-9 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 border border-transparent hover:border-destructive/20 shrink-0"
                                        title="Disconnect Account"
                                    >
                                        <LogOut className="w-4 h-4" />
                                    </Button>
                                </>
                            )}
                        </div>
                    </div>

                    {/* User Info Section */}
                    {isConnected && (
                        <div className="flex items-center gap-3 py-3 border-b border-sidebar-border min-w-0">
                            <img
                                src={userPicture}
                                alt={userName}
                                className="w-9 h-9 rounded-full border border-sidebar-border shrink-0"
                            />
                            <div className="min-w-0 flex-1">
                                <p className="text-[0.85rem] font-bold text-foreground truncate">{userName}</p>
                                <p className="text-[0.7rem] text-muted-foreground truncate">{userEmail}</p>
                            </div>
                        </div>
                    )}

                    {/* File List / Breadcrumbs */}
                    {isConnected && (
                        <div className="space-y-2 min-w-0 overflow-hidden">
                            {/* Breadcrumbs */}
                            <div className="flex items-center flex-wrap gap-x-1 gap-y-1 px-1 min-w-0">
                                {breadcrumbs.map((b, i) => (
                                    <div key={b.id} className="flex items-center min-w-0 max-w-full">
                                        {i > 0 && <ChevronRight className="w-3 h-3 text-muted-foreground/30 mx-0.5 shrink-0" />}
                                        <button
                                            onClick={() => navigateToBreadcrumb(i)}
                                            className={cn(
                                                'text-[0.85rem] transition-colors truncate max-w-full',
                                                i === breadcrumbs.length - 1
                                                    ? 'font-bold text-foreground'
                                                    : 'text-muted-foreground hover:text-primary'
                                            )}
                                        >
                                            {b.name}
                                        </button>
                                    </div>
                                ))}
                            </div>

                            {isDriveLoading ? (
                                <div className="flex flex-col items-center justify-center py-10 gap-3 text-muted-foreground">
                                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                                    <span className="text-xs">Loading files...</span>
                                </div>
                            ) : (
                                <DriveFileList items={driveItems} onFolderClick={handleFolderClick} />
                            )}
                        </div>
                    )}
                </div>
            </ScrollArea>
        </aside>
    )
}
