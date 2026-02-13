"use client"

import Link from "next/link"
import { IconAlertTriangle } from "@tabler/icons-react"

import { Button } from "@/components/ui/button"

export function ErrorState({
  title,
  description,
  onRetry,
  retryLabel = "Reessayer",
  secondaryLabel,
  secondaryHref,
  onSecondaryAction,
}: {
  title: string
  description?: string
  onRetry?: () => void
  retryLabel?: string
  secondaryLabel?: string
  secondaryHref?: string
  onSecondaryAction?: () => void
}) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center rounded-xl border border-red-300/60 bg-red-50/90 px-6 py-8 text-center shadow-sm dark:border-red-900/60 dark:bg-red-950/40">
      <IconAlertTriangle className="mb-2 size-7 text-red-700 dark:text-red-300" />
      <h3 className="text-sm font-semibold text-red-950 dark:text-red-100">{title}</h3>
      {description ? (
        <p className="mt-1 max-w-xl text-sm text-red-800 dark:text-red-200">{description}</p>
      ) : null}
      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        {onRetry ? (
          <Button variant="outline" className="border-red-300 bg-white/70 hover:bg-red-100 dark:border-red-700 dark:bg-red-900/30 dark:hover:bg-red-900/50" onClick={onRetry}>
            {retryLabel}
          </Button>
        ) : null}
        {secondaryLabel && secondaryHref ? (
          <Button variant="ghost" asChild>
            <Link href={secondaryHref}>{secondaryLabel}</Link>
          </Button>
        ) : null}
        {secondaryLabel && onSecondaryAction ? (
          <Button variant="ghost" onClick={onSecondaryAction}>
            {secondaryLabel}
          </Button>
        ) : null}
      </div>
    </div>
  )
}
