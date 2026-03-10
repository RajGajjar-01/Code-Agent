import { useState } from 'react'
import { useNavigate } from 'react-router'
import { Loader2, LogOut, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useUserStore } from '@/stores/user-store'

export function ProfilePage() {
    const navigate = useNavigate()
    const { name, email, logout } = useUserStore()
    const [isLoggingOut, setIsLoggingOut] = useState(false)

    const handleLogout = async () => {
        setIsLoggingOut(true)
        try {
            await logout()
            navigate('/login', { replace: true })
        } finally {
            setIsLoggingOut(false)
        }
    }

    return (
        <div className="flex-1 min-w-0 h-screen overflow-y-auto bg-background">
            <div className="max-w-2xl mx-auto px-5 py-8 space-y-6">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                        <User className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="min-w-0">
                        <h1 className="text-xl font-bold tracking-tight truncate">Profile</h1>
                        <p className="text-sm text-muted-foreground truncate">Manage your account session</p>
                    </div>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-base">Account</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Name</div>
                            <div className="text-sm font-medium break-words">{name || '—'}</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Email</div>
                            <div className="text-sm font-medium break-words">{email || '—'}</div>
                        </div>

                        <div className="pt-2">
                            <Button
                                variant="destructive"
                                onClick={handleLogout}
                                disabled={isLoggingOut}
                                className="gap-2"
                            >
                                {isLoggingOut ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Logging out...
                                    </>
                                ) : (
                                    <>
                                        <LogOut className="h-4 w-4" />
                                        Logout
                                    </>
                                )}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
