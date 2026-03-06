import { useEffect, useState } from 'react'
import { LogOut, FolderOpen, Loader2, ChevronRight, X, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DriveFileList } from '@/components/drive/drive-file-list'
import { useAuthStore } from '@/stores/auth-store'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useChatStore } from '@/stores/chat-store'
import { authApi, wpCliApi, wpSitesApi } from '@/lib/axios'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { useSettingsStore } from '@/stores/settings-store'
import driveLogo from '@/assets/google-drive.svg'
import wordpressLogo from '@/assets/wordpress.svg'
import { toast } from 'sonner'
import type { WordPressSite } from '@/types'

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
    const { loadConversations } = useChatStore()

    const {
        wpCliWpPath,
        setWpCliWpPath,
        wpCliDefaultUrl,
        setWpCliDefaultUrl,
        activeWpSiteId,
        setActiveWpSiteId,
    } = useSettingsStore()
    const [wpCliOpen, setWpCliOpen] = useState(false)
    const [wpCliValidating, setWpCliValidating] = useState(false)
    const [wpCliValidated, setWpCliValidated] = useState(false)

    const [wpSites, setWpSites] = useState<WordPressSite[]>([])
    const [wpSitesLoading, setWpSitesLoading] = useState(false)
    const [wpSitesOpen, setWpSitesOpen] = useState(false)
    const [wpSiteName, setWpSiteName] = useState('')
    const [wpSiteUrl, setWpSiteUrl] = useState('')
    const [wpSiteUsername, setWpSiteUsername] = useState('')
    const [wpSiteAppPassword, setWpSiteAppPassword] = useState('')
    const [wpSiteSaving, setWpSiteSaving] = useState(false)

    const wpCliPathTrimmed = (wpCliWpPath || '').trim()

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
            loadConversations()
        }
    }, [isConnected, userEmail])

    useEffect(() => {
        if (!connectorsPanelOpen) return
        if (!userEmail) return
        if (wpSitesLoading) return

        ;(async () => {
            setWpSitesLoading(true)
            try {
                const { data } = await wpSitesApi.list()
                setWpSites(data)
                if (activeWpSiteId != null && !data.some((s) => s.id === activeWpSiteId)) {
                    setActiveWpSiteId(null)
                }
            } catch {
                setWpSites([])
            } finally {
                setWpSitesLoading(false)
            }
        })()
    }, [connectorsPanelOpen, userEmail, wpSitesLoading, activeWpSiteId, setActiveWpSiteId])

    const handleFolderClick = (id: string, name: string) => {
        useAuthStore.setState((s) => ({
            breadcrumbs: [...s.breadcrumbs, { id, name }],
        }))
        loadFolder(id)
    }

    if (!connectorsPanelOpen) return null

    return (
        <aside className="w-full flex-col h-full bg-sidebar overflow-hidden flex min-w-0" role="complementary" aria-label="Connectors sidebar">
            <div className="flex items-center justify-between h-[60px] px-5 border-b border-sidebar-border bg-sidebar shrink-0 min-w-0">
                <h3 className="text-[0.95rem] font-bold truncate text-sidebar-foreground">Connectors</h3>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleConnectorsPanel}
                    className="h-6 w-6 hover:bg-sidebar-accent shrink-0"
                    aria-label="Close connectors panel"
                    aria-expanded={connectorsPanelOpen}
                    aria-controls="connectors-panel-content"
                >
                    <X className="h-4 w-4" />
                </Button>
            </div>

            <div className="p-4 space-y-4 shrink-0 border-b border-sidebar-border/50">
                <div className="bg-background border border-sidebar-border rounded-lg p-4 shadow-sm transition-all hover:border-primary/50 group overflow-hidden">
                    <div className="flex justify-between items-start gap-2 mb-4 min-w-0">
                        <div className="flex-1 min-w-0 text-left">
                            <h4 className="text-[0.9rem] font-bold text-foreground truncate">Google Drive</h4>
                            <p className="text-[0.75rem] text-muted-foreground mt-0.5 break-words">
                                {isConnected ? 'Account connected successfully.' : 'Connect and access your files.'}
                            </p>
                        </div>
                        <div className="w-11 h-11 flex items-center justify-center bg-secondary rounded-md shrink-0">
                            <img src={driveLogo} alt="Google Drive" className="w-8 h-8" />
                        </div>
                    </div>

                    <div className="flex gap-2 w-full min-w-0">
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
                                    <span className="truncate pointer-events-none">Browse Files</span>
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

                <div className="bg-background border border-sidebar-border rounded-lg p-4 shadow-sm transition-all hover:border-primary/50 group overflow-hidden">
                    <div className="flex justify-between items-start gap-2 mb-4 min-w-0">
                        <div className="flex-1 min-w-0 text-left">
                            <h4 className="text-[0.9rem] font-bold text-foreground truncate">WordPress Sites</h4>
                            <p className="text-[0.75rem] text-muted-foreground mt-0.5 break-words">
                                Connect one or more WordPress sites using an application password.
                            </p>
                        </div>
                        <div className="w-11 h-11 flex items-center justify-center bg-secondary rounded-md shrink-0">
                            <img src={wordpressLogo} alt="WordPress" className="w-8 h-8" />
                        </div>
                    </div>

                    <div className="flex gap-2 w-full min-w-0">
                        <Button
                            variant={wpSitesOpen ? 'outline' : 'default'}
                            className={cn(
                                'flex-1 h-9 rounded-lg text-[0.8rem] font-bold truncate',
                                wpSitesOpen ? 'border-black text-black bg-primary/5 hover:bg-primary hover:text-black hover:border-primary' : '',
                            )}
                            disabled={wpSiteSaving}
                            onClick={() => setWpSitesOpen((v) => !v)}
                        >
                            {wpSitesOpen ? 'Close' : 'Manage'}
                        </Button>
                    </div>

                    <div className="pt-3 space-y-2">
                        {wpSitesLoading ? (
                            <div className="flex items-center justify-center py-2 text-muted-foreground">
                                <Loader2 className="w-4 h-4 animate-spin" />
                            </div>
                        ) : wpSites.length ? (
                            wpSites.slice(0, wpSitesOpen ? wpSites.length : 3).map((s) => {
                                const isActive = activeWpSiteId === s.id
                                const title = (s.name || s.base_url || '').toString()
                                return (
                                    <div
                                        key={s.id}
                                        className={cn(
                                            'flex items-center gap-2 border rounded-md px-2 py-2 min-w-0',
                                            isActive ? 'border-primary bg-primary/5' : 'border-sidebar-border',
                                        )}
                                    >
                                        <button
                                            className="flex-1 min-w-0 text-left"
                                            onClick={() => setActiveWpSiteId(isActive ? null : s.id)}
                                            title={title}
                                        >
                                            <div className="flex items-center gap-2 min-w-0">
                                                <div className="text-[0.8rem] font-bold text-foreground truncate">
                                                    {s.name || s.base_url}
                                                </div>
                                                {isActive && (
                                                    <span className="text-[0.65rem] font-bold px-1.5 py-0.5 rounded bg-primary text-primary-foreground shrink-0">
                                                        Active
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-[0.7rem] text-muted-foreground truncate">{s.username}</div>
                                        </button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                            onClick={async () => {
                                                try {
                                                    await wpSitesApi.remove(s.id)
                                                    setWpSites((prev) => prev.filter((x) => x.id !== s.id))
                                                    if (activeWpSiteId === s.id) {
                                                        setActiveWpSiteId(null)
                                                    }
                                                } catch {
                                                    toast.error('Failed to delete site')
                                                }
                                            }}
                                            title="Delete"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                )
                            })
                        ) : (
                            <div className="text-[0.75rem] text-muted-foreground">No sites connected yet.</div>
                        )}

                        {!wpSitesOpen && wpSites.length > 3 && (
                            <div className="text-[0.72rem] text-muted-foreground">+{wpSites.length - 3} more</div>
                        )}
                    </div>

                    {wpSitesOpen && (
                        <div className="mt-4 space-y-3">
                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-foreground">Site name (optional)</label>
                                <Input
                                    placeholder="My Blog"
                                    value={wpSiteName}
                                    onChange={(e) => setWpSiteName(e.target.value)}
                                    className="h-9"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-foreground">Site URL</label>
                                <Input
                                    placeholder="https://example.com"
                                    value={wpSiteUrl}
                                    onChange={(e) => setWpSiteUrl(e.target.value)}
                                    className="h-9"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-foreground">Username</label>
                                <Input
                                    placeholder="admin"
                                    value={wpSiteUsername}
                                    onChange={(e) => setWpSiteUsername(e.target.value)}
                                    className="h-9"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-foreground">Application password</label>
                                <Input
                                    placeholder="xxxx xxxx xxxx xxxx"
                                    value={wpSiteAppPassword}
                                    onChange={(e) => setWpSiteAppPassword(e.target.value)}
                                    className="h-9"
                                    type="password"
                                    autoComplete="new-password"
                                />
                            </div>

                            <Button
                                className="w-full h-9 rounded-lg text-[0.8rem] font-bold"
                                disabled={wpSiteSaving}
                                onClick={async () => {
                                    const baseUrl = (wpSiteUrl || '').trim()
                                    const username = (wpSiteUsername || '').trim()
                                    const appPassword = (wpSiteAppPassword || '').trim()

                                    if (!baseUrl) {
                                        toast.error('Site URL is required')
                                        return
                                    }
                                    if (!username) {
                                        toast.error('Username is required')
                                        return
                                    }
                                    if (!appPassword) {
                                        toast.error('Application password is required')
                                        return
                                    }

                                    setWpSiteSaving(true)
                                    try {
                                        const { data } = await wpSitesApi.create({
                                            name: (wpSiteName || '').trim() || null,
                                            base_url: baseUrl,
                                            username,
                                            app_password: appPassword,
                                        })
                                        setWpSites((prev) => [data, ...prev])
                                        setActiveWpSiteId(data.id)
                                        setWpSiteName('')
                                        setWpSiteUrl('')
                                        setWpSiteUsername('')
                                        setWpSiteAppPassword('')
                                        toast.success('WordPress site connected')
                                    } catch {
                                        toast.error('Failed to connect site. Make sure the backend is running.')
                                    } finally {
                                        setWpSiteSaving(false)
                                    }
                                }}
                            >
                                {wpSiteSaving ? 'Saving...' : 'Add site'}
                            </Button>
                        </div>
                    )}
                </div>

                <div className="bg-background border border-sidebar-border rounded-lg p-4 shadow-sm transition-all hover:border-primary/50 group overflow-hidden">
                    <div className="flex justify-between items-start gap-2 mb-4 min-w-0">
                        <div className="flex-1 min-w-0 text-left">
                            <h4 className="text-[0.9rem] font-bold text-foreground truncate">WP-CLI</h4>
                            <p className="text-[0.75rem] text-muted-foreground mt-0.5 break-words">
                                Configure local WordPress path for WP-CLI tools.
                            </p>
                        </div>
                        <div className="w-11 h-11 flex items-center justify-center bg-secondary rounded-md shrink-0">
                            <span className="text-[0.9rem] font-bold text-foreground">WP</span>
                        </div>
                    </div>

                    <div className="flex gap-2 w-full min-w-0">
                        <Button
                            variant={wpCliOpen ? 'outline' : 'default'}
                            className={cn(
                                'flex-1 h-9 rounded-lg text-[0.8rem] font-bold truncate',
                                wpCliOpen ? 'border-black text-black bg-primary/5 hover:bg-primary hover:text-black hover:border-primary' : '',
                            )}
                            disabled={wpCliValidating}
                            onClick={async () => {
                                if (!wpCliOpen) {
                                    setWpCliOpen(true)
                                    return
                                }

                                if (!wpCliPathTrimmed) {
                                    toast.error('Please enter the WP filesystem path first')
                                    return
                                }

                                setWpCliValidating(true)
                                try {
                                    const { data } = await wpCliApi.validatePath(wpCliPathTrimmed)
                                    if (data.valid) {
                                        setWpCliValidated(true)
                                        toast.success(data.detail || 'WP-CLI configured')
                                        setWpCliOpen(false)
                                    } else {
                                        setWpCliValidated(false)
                                        toast.error(data.detail || 'Invalid WordPress folder')
                                    }
                                } catch {
                                    setWpCliValidated(false)
                                    toast.error('Validation failed. Make sure the backend is running.')
                                } finally {
                                    setWpCliValidating(false)
                                }
                            }}
                        >
                            {wpCliValidating
                                ? 'Validating...'
                                : wpCliOpen
                                    ? (wpCliPathTrimmed ? 'Validate' : 'Connect')
                                    : (wpCliValidated ? 'Connected' : 'Configure')}
                        </Button>
                    </div>

                    {wpCliOpen && (
                        <div className="mt-4 space-y-3">
                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-foreground">WP filesystem path</label>
                                <Input
                                    placeholder="/var/www/html"
                                    value={wpCliWpPath}
                                    onChange={(e) => {
                                        setWpCliValidated(false)
                                        setWpCliWpPath(e.target.value)
                                    }}
                                    className="h-9"
                                />
                                <p className="text-[0.72rem] text-muted-foreground">
                                    Folder that contains <span className="font-mono">wp-config.php</span>
                                </p>
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-foreground">Default site URL (optional)</label>
                                <Input
                                    placeholder="https://example.com"
                                    value={wpCliDefaultUrl}
                                    onChange={(e) => setWpCliDefaultUrl(e.target.value)}
                                    className="h-9"
                                />
                            </div>
                        </div>
                    )}
                </div>

                {isConnected && (
                    <div className="flex items-center gap-3 py-1 min-w-0">
                        <img
                            src={userPicture}
                            alt={userName}
                            className="w-8 h-8 rounded-full border border-sidebar-border shrink-0"
                        />
                        <div className="min-w-0 flex-1">
                            <p className="text-[0.8rem] font-bold text-foreground truncate">{userName}</p>
                            <p className="text-[0.65rem] text-muted-foreground truncate">{userEmail}</p>
                        </div>
                    </div>
                )}

                {isConnected && (
                    <div className="flex items-center flex-wrap gap-x-1 gap-y-1 px-1 min-w-0 border-t border-sidebar-border/30 pt-4">
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
                )}
            </div>

            <div
                className="flex-1 w-full min-h-0 overflow-y-auto overscroll-contain"
                id="connectors-panel-content"
                role="region"
                aria-label="Connectors panel content"
            >
                <div className="p-4 pt-1 space-y-4 min-w-0">
                    {isConnected && (
                        <div className="space-y-4 min-w-0 overflow-hidden">
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
            </div>
        </aside >
    )
}
