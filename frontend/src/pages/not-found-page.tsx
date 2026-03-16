import { Link } from 'react-router'
import { Layers, Home, ArrowLeft, FileQuestion } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">
            <div className="w-full max-w-md text-center space-y-8">
                {/* Logo */}
                <div className="flex flex-col items-center gap-3">
                    <div className="h-14 w-14 rounded-lg bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
                        <Layers className="h-7 w-7 text-black" />
                    </div>
                </div>

                {/* 404 Illustration */}
                <div className="space-y-4">
                    <div className="relative">
                        <FileQuestion className="h-32 w-32 mx-auto text-muted-foreground/30" />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-6xl font-bold text-muted-foreground/50">
                                404
                            </span>
                        </div>
                    </div>
                </div>

                {/* Message */}
                <div className="space-y-2">
                    <h1 className="text-2xl font-bold tracking-tight">
                        Page Not Found
                    </h1>
                    <p className="text-muted-foreground">
                        Sorry, we couldn't find the page you're looking for.
                        <br />
                        It might have been moved or doesn't exist.
                    </p>
                </div>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Button
                        variant="outline"
                        className="gap-2"
                        onClick={() => window.history.back()}
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Go Back
                    </Button>
                    <Button asChild className="gap-2">
                        <Link to="/">
                            <Home className="h-4 w-4" />
                            Back to Home
                        </Link>
                    </Button>
                </div>

                {/* Help text */}
                <p className="text-sm text-muted-foreground">
                    If you think this is an error, please{' '}
                    <a
                        href="mailto:support@example.com"
                        className="text-primary hover:underline underline-offset-4"
                    >
                        contact support
                    </a>
                </p>
            </div>
        </div>
    )
}
