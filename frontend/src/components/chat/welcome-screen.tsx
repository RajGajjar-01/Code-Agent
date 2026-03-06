import { Layers, FileText, List, Info, PenLine } from 'lucide-react'

const suggestions = [
    {
        icon: FileText,
        text: 'Create a landing page',
        detail: 'Hero, services & contact form',
        prompt: 'Create a new WordPress page with a hero section, services grid, and contact form',
    },
    {
        icon: List,
        text: 'List all pages',
        detail: 'View existing WordPress content',
        prompt: 'List all pages on my WordPress site',
    },
    {
        icon: Info,
        text: 'Get site info',
        detail: 'Site name, URL & all pages',
        prompt: 'Get my WordPress site info and list all existing pages',
    },
    {
        icon: PenLine,
        text: 'Write a blog post',
        detail: 'SEO optimized content',
        prompt: 'Create a blog post about plumbing services in Pompano Beach with SEO optimized content',
    },
]

interface WelcomeScreenProps {
    onSuggestionClick: (prompt: string) => void
}

export function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
    return (
        <div className="flex flex-col items-center justify-start min-h-full px-6 py-20 text-center animate-in fade-in duration-500">
            {/* Floating icon */}
            <div className="mb-5 p-4 bg-secondary border rounded-lg animate-bounce [animation-duration:3s] [animation-timing-function:ease-in-out]">
                <Layers className="h-12 w-12" />
            </div>

            <h2 className="text-[1.75rem] font-bold tracking-[-0.03em] mb-2">WordPress Agent</h2>
            <p className="text-sm text-muted-foreground max-w-[480px] leading-relaxed mb-9">
                AI-powered WordPress site builder. I can create pages, posts, manage
                content, and download assets from existing sites.
            </p>

            {/* Suggestion grid — 2 columns, 1 on small screens */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-[560px]">
                {suggestions.map((s) => (
                    <button
                        key={s.text}
                        onClick={() => onSuggestionClick(s.prompt)}
                        className="flex flex-col items-start gap-1.5 p-4 bg-card border rounded-lg text-left cursor-pointer transition-all hover:-translate-y-0.5 hover:border-primary hover:bg-primary/20 hover:shadow-md min-w-0 overflow-hidden"
                    >
                        <s.icon className="h-5 w-5 text-muted-foreground shrink-0" />
                        <span className="text-[0.85rem] font-medium text-black leading-snug break-words w-full">{s.text}</span>
                        <span className="text-[0.75rem] text-muted-foreground break-words w-full">{s.detail}</span>
                    </button>
                ))}
            </div>
        </div>
    )
}
