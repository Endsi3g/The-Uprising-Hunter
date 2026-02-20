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
    <div role="alert" className="flex min-h-40 flex-col items-start justify-center rounded-xl border-l-4 border-l-red-500 border-red-300/60 bg-red-50/90 px-6 py-6 text-left shadow-md transition-all dark:border-l-red-500 dark:border-red-900/60 dark:bg-red-950/40">
      <div className="flex items-center gap-3 mb-3 shrink-0">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/50">
          <IconAlertTriangle className="size-5 text-red-700 dark:text-red-400" aria-hidden="true" />
        </div>
        <h3 className="text-base font-semibold text-red-950 dark:text-red-100">{title}</h3>
      </div>
      {description ? (
        <div className="pl-13 w-full">
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-red-800 dark:text-red-200">{description}</p>
        </div>
      ) : null}
      <div className="mt-5 pl-13 flex flex-wrap items-center gap-3 w-full">
        {onRetry ? (
          <Button variant="outline" size="sm" className="border-red-300 bg-white/80 hover:bg-red-100 dark:border-red-700 dark:bg-red-900/40 dark:hover:bg-red-900/60 shadow-sm" onClick={onRetry}>
            {retryLabel}
          </Button>
        ) : null}
        {secondaryLabel && secondaryHref ? (
          <Button variant="ghost" size="sm" asChild className="text-red-900 hover:bg-red-100/50 hover:text-red-950 dark:text-red-100 dark:hover:bg-red-900/30 dark:hover:text-red-50">
            <Link href={secondaryHref}>{secondaryLabel}</Link>
          </Button>
        ) : null}
        {secondaryLabel && onSecondaryAction ? (
          <Button variant="ghost" size="sm" className="text-red-900 hover:bg-red-100/50 hover:text-red-950 dark:text-red-100 dark:hover:bg-red-900/30 dark:hover:text-red-50" onClick={onSecondaryAction}>
            {secondaryLabel}
          </Button>
        ) : null}
      </div>
    </div>
  )
}
