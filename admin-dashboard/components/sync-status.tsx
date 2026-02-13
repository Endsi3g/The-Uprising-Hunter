"use client"

import * as React from "react"
import { IconRefresh, IconRefreshAlert } from "@tabler/icons-react"
import { toast } from "sonner"

import { useSyncSettings } from "@/components/app-providers"
import { Button } from "@/components/ui/button"
import { formatDateTimeFr } from "@/lib/format"

export function SyncStatus({
  updatedAt,
  isValidating,
  onRefresh,
}: {
  updatedAt?: Date | null
  isValidating?: boolean
  onRefresh?: () => void
}) {
  const { refreshSeconds } = useSyncSettings()
  const [nowMs, setNowMs] = React.useState(0)

  React.useEffect(() => {
    setNowMs(Date.now())
    const intervalId = window.setInterval(() => setNowMs(Date.now()), 30_000)
    return () => window.clearInterval(intervalId)
  }, [])

  const staleMs = React.useMemo(() => {
    if (!updatedAt) return Number.MAX_SAFE_INTEGER
    return nowMs - updatedAt.getTime()
  }, [nowMs, updatedAt])

  const isStale = staleMs > Math.max(refreshSeconds * 2000, 60_000)

  if (isStale) {
    return (
      <div className="mb-4 flex w-full items-center justify-between rounded-md border border-amber-500/55 bg-amber-400/16 px-3 py-2 dark:border-amber-400/45 dark:bg-amber-300/12">
        <div className="flex items-center gap-2 text-sm font-medium text-amber-950 dark:text-amber-50">
          <IconRefreshAlert className="size-4" />
          <span>
            Donnees potentiellement perimees -{" "}
            {updatedAt ? formatDateTimeFr(updatedAt.toISOString()) : "Aucune synchronisation valide"}
          </span>
        </div>
        {onRefresh ? (
          <Button
            variant="outline"
            size="sm"
            className="h-7 border-amber-600/55 bg-amber-50 text-xs text-amber-950 hover:bg-amber-100 dark:border-amber-300/35 dark:bg-amber-200/15 dark:text-amber-50 dark:hover:bg-amber-200/25"
            onClick={() => {
              onRefresh()
              toast.success("Donnees rafraichies")
            }}
          >
            Rafraichir
          </Button>
        ) : null}
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <IconRefresh className={`size-3.5 ${isValidating ? "animate-spin" : ""}`} />
      {updatedAt ? (
        <span>Donnees a jour - {formatDateTimeFr(updatedAt.toISOString())}</span>
      ) : (
        <span>Synchronisation en attente</span>
      )}
    </div>
  )
}
