
import * as React from "react"
import fs from "fs"
import path from "path"
import { format } from "date-fns"
import { fr } from "date-fns/locale"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { AppShell } from "@/components/layout/app-shell"

type Commit = {
    hash: string
    date: string
    author: string
    message: string
}

function getChangelog(): Commit[] {
    try {
        const filePath = path.join(process.cwd(), "public", "changelog.json")
        const content = fs.readFileSync(filePath, "utf8")
        return JSON.parse(content)
    } catch (error) {
        console.error("Failed to read changelog:", error)
        return []
    }
}

export default function ChangelogPage() {
    const commits = getChangelog()

    return (
        <AppShell contentClassName="gap-6">
            <div className="flex flex-col space-y-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Historique des versions</h2>
                    <p className="text-muted-foreground">
                        Les modifications les plus rÃ©centes du projet.
                    </p>
                </div>
                <Separator className="my-4" />
                <ScrollArea className="h-[calc(100vh-220px)] rounded-md border p-4">
                    <div className="space-y-8">
                        {commits.map((commit, index) => (
                            <div key={commit.hash} className="flex gap-4">
                                <div className="flex flex-col items-center">
                                    <div className="relative flex h-3 w-3 items-center justify-center rounded-full border border-primary bg-background shadow-sm">
                                        <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                                    </div>
                                    {index !== commits.length - 1 && (
                                        <div className="w-px flex-1 bg-border" />
                                    )}
                                </div>
                                <div className="flex flex-1 flex-col gap-1 pb-8">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium text-muted-foreground">
                                            {format(new Date(commit.date), "dd MMMM yyyy", { locale: fr })}
                                        </span>
                                        <Badge variant="outline" className="font-mono text-xs">
                                            {commit.hash}
                                        </Badge>
                                    </div>
                                    <p className="font-medium leading-none">{commit.message}</p>
                                    <p className="text-xs text-muted-foreground">
                                        par {commit.author}
                                    </p>
                                </div>
                            </div>
                        ))}
                        {commits.length === 0 && (
                            <div className="text-center text-muted-foreground">
                                Aucun changement rÃ©cent trouvÃ©.
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </div>
        </AppShell>
    )
}
