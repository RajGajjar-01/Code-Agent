import { useState } from 'react'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface CreateModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    parentPath: string
    type: 'file' | 'directory'
    onSubmit: (parentPath: string, name: string, type: string) => Promise<{ error?: string }>
}

export function CreateModal({ open, onOpenChange, parentPath, type, onSubmit }: CreateModalProps) {
    const [name, setName] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleSubmit = async () => {
        if (!name.trim()) return
        setIsSubmitting(true)
        const result = await onSubmit(parentPath, name.trim(), type)
        setIsSubmitting(false)
        if (!result.error) {
            setName('')
            onOpenChange(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-sm">
                <DialogHeader>
                    <DialogTitle>Create New {type === 'file' ? 'File' : 'Folder'}</DialogTitle>
                </DialogHeader>

                <Input
                    placeholder={type === 'file' ? 'style.css' : 'new-folder'}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                    autoFocus
                />

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleSubmit} disabled={!name.trim() || isSubmitting}>
                        Create
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
