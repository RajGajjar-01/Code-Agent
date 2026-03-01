import Editor, { type OnMount } from '@monaco-editor/react'
import { useRef, useCallback } from 'react'

interface CodeEditorProps {
    value: string
    language: string
    wordWrap: boolean
    onChange: (value: string) => void
    onSave: () => void
}

export function CodeEditor({ value, language, wordWrap, onChange, onSave }: CodeEditorProps) {
    const editorRef = useRef<Parameters<OnMount>[0] | null>(null)

    const handleMount: OnMount = useCallback(
        (editor) => {
            editorRef.current = editor

            // Ctrl+S shortcut
            editor.addCommand(
                // eslint-disable-next-line no-bitwise
                (window.monaco?.KeyMod?.CtrlCmd ?? 2048) | (window.monaco?.KeyCode?.KeyS ?? 49),
                () => onSave(),
            )
        },
        [onSave],
    )

    return (
        <Editor
            height="100%"
            language={language}
            value={value}
            onChange={(v) => onChange(v || '')}
            onMount={handleMount}
            theme="light"
            options={{
                fontFamily: "'Fira Code', 'Cascadia Code', monospace",
                fontSize: 14,
                minimap: { enabled: true },
                wordWrap: wordWrap ? 'on' : 'off',
                bracketPairColorization: { enabled: true },
                formatOnPaste: true,
                scrollBeyondLastLine: false,
                padding: { top: 12 },
                smoothScrolling: true,
                cursorBlinking: 'smooth',
                automaticLayout: true,
            }}
        />
    )
}

// Extend window for monaco types
declare global {
    interface Window {
        monaco?: {
            KeyMod?: { CtrlCmd: number }
            KeyCode?: { KeyS: number }
        }
    }
}
