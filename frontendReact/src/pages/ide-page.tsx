import { useEffect, useState, useCallback } from 'react'
import { toast } from 'sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar'
import { IdeHeader } from '@/components/ide/ide-header'
import { IdeSidebar } from '@/components/ide/ide-sidebar'
import { EditorTabs } from '@/components/ide/editor-tabs'
import { CodeEditor } from '@/components/ide/code-editor'
import { IdeWelcome } from '@/components/ide/ide-welcome'
import { CreateModal } from '@/components/ide/create-modal'
import { useIdeStore } from '@/stores/ide-store'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useSidebarShortcuts } from '@/hooks/use-sidebar-shortcuts'

export function IdePage() {
    const {
        openTabs,
        activePath,
        loadRoots,
        activateTab,
        closeTab,
        saveFile,
        createNode,
    } = useIdeStore()

    const { ideSidebarOpen, setIdeSidebarOpen } = useSidebarStore()

    const [wordWrap, setWordWrap] = useState(false)
    const [createModalState, setCreateModalState] = useState<{
        open: boolean
        parentPath: string
        type: 'file' | 'directory'
    }>({ open: false, parentPath: '', type: 'file' })

    // Enable keyboard shortcuts
    useSidebarShortcuts()

    useEffect(() => {
        loadRoots()
    }, [loadRoots])

    // Ctrl+S global shortcut
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault()
                handleSave()
            }
        }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    })

    const activeTab = activePath ? openTabs.get(activePath) : undefined

    const handleSave = useCallback(async () => {
        if (!activePath || !activeTab) {
            toast.info('No file open')
            return
        }
        const { error } = await saveFile(activePath, activeTab.content)
        if (error) {
            toast.error(`Save failed — ${error}`)
        } else {
            toast.success('Saved ✓')
        }
    }, [activePath, activeTab, saveFile])

    const handleEditorChange = useCallback(
        (value: string) => {
            if (!activePath) return
            // Update the tab content in the store
            useIdeStore.setState((s) => {
                const next = new Map(s.openTabs)
                const tab = next.get(activePath)
                if (tab) {
                    next.set(activePath, { ...tab, content: value, isDirty: value !== tab.savedContent })
                }
                return { openTabs: next }
            })
        },
        [activePath],
    )

    const handleCreateSubmit = async (parentPath: string, name: string, type: string) => {
        const result = await createNode(parentPath, name, type)
        if (result.error) {
            toast.error(result.error)
        } else {
            toast.success(`Created: ${name}`)
        }
        return result
    }

    return (
        <TooltipProvider>
            <SidebarProvider open={ideSidebarOpen} onOpenChange={setIdeSidebarOpen}>
                <IdeSidebar
                    onCreateRequest={(parentPath, type) =>
                        setCreateModalState({ open: true, parentPath, type })
                    }
                />
                <SidebarInset>
                    <div className="flex h-screen flex-col bg-background">
                        <IdeHeader
                            fileInfo={activePath || ''}
                            wordWrap={wordWrap}
                            onToggleWrap={() => setWordWrap((v) => !v)}
                            onSave={handleSave}
                        />

                        <main className="flex flex-1 flex-col min-w-0 overflow-hidden">
                            <EditorTabs
                                tabs={openTabs}
                                activePath={activePath}
                                onActivate={activateTab}
                                onClose={closeTab}
                            />

                            <div className="flex-1 overflow-hidden">
                                {activeTab ? (
                                    <CodeEditor
                                        value={activeTab.content}
                                        language={activeTab.language}
                                        wordWrap={wordWrap}
                                        onChange={handleEditorChange}
                                        onSave={handleSave}
                                    />
                                ) : (
                                    <IdeWelcome />
                                )}
                            </div>
                        </main>

                        <CreateModal
                            open={createModalState.open}
                            onOpenChange={(open) => setCreateModalState((s) => ({ ...s, open }))}
                            parentPath={createModalState.parentPath}
                            type={createModalState.type}
                            onSubmit={handleCreateSubmit}
                        />
                    </div>
                </SidebarInset>
            </SidebarProvider>
        </TooltipProvider>
    )
}
