import { Bot, Check, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useSettingsStore, type LLMProvider } from '@/stores/settings-store'

const MODEL_INFO: Record<
    LLMProvider,
    { name: string; description: string }
> = {
    groq: {
        name: 'Groq (Llama 3.3 70B)',
        description: 'Fast inference, great for general tasks',
    },
    glm5: {
        name: 'GLM-5 (Z.AI)',
        description: 'Optimized for agentic tasks & long-horizon planning',
    },
    gemini: {
        name: 'Gemini 2.5 Flash',
        description: 'Google\'s latest model with advanced reasoning',
    },
}

export function ModelSelector() {
    const { llmProvider, setLLMProvider } = useSettingsStore()
    const currentModel = MODEL_INFO[llmProvider]

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className="gap-2 h-9 px-3 text-sm font-medium"
                >
                    <Bot className="h-4 w-4" />
                    <span className="hidden sm:inline">{currentModel.name.split(' ')[0]}</span>
                    <ChevronDown className="h-3.5 w-3.5 opacity-50" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[280px]">
                <DropdownMenuLabel>Select AI Model</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {(Object.keys(MODEL_INFO) as LLMProvider[]).map((provider) => {
                    const model = MODEL_INFO[provider]
                    const isSelected = provider === llmProvider

                    return (
                        <DropdownMenuItem
                            key={provider}
                            onClick={() => setLLMProvider(provider)}
                            className="flex items-start gap-3 py-3 cursor-pointer"
                        >
                            <div className="flex h-5 w-5 items-center justify-center shrink-0">
                                {isSelected ? (
                                    <Check className="h-4 w-4 text-primary" />
                                ) : (
                                    <Bot className="h-4 w-4 text-muted-foreground" />
                                )}
                            </div>
                            <div className="flex-1 space-y-1">
                                <div className="font-medium text-sm">{model.name}</div>
                                <div className="text-xs text-muted-foreground">
                                    {model.description}
                                </div>
                            </div>
                        </DropdownMenuItem>
                    )
                })}
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
