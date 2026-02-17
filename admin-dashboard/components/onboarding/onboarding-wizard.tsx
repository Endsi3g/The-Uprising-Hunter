"use client"

import * as React from "react"

import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

export type OnboardingStep = {
  id: string
  title: string
  description: string
  href: string
  ctaLabel: string
}

type OnboardingWizardProps = {
  open: boolean
  saving: boolean
  stepIndex: number
  steps: OnboardingStep[]
  progressLabel: string
  previousLabel: string
  nextLabel: string
  skipLabel: string
  finishLabel: string
  onOpenChange: (open: boolean) => void
  onPrevious: () => void
  onNext: () => void
  onSkip: () => void
  onFinish: () => void
  onNavigate: (href: string) => void
}

export function OnboardingWizard({
  open,
  saving,
  stepIndex,
  steps,
  progressLabel,
  previousLabel,
  nextLabel,
  skipLabel,
  finishLabel,
  onOpenChange,
  onPrevious,
  onNext,
  onSkip,
  onFinish,
  onNavigate,
}: OnboardingWizardProps) {
  const safeIndex = Math.max(0, Math.min(stepIndex, Math.max(steps.length - 1, 0)))
  const currentStep = steps[safeIndex]
  const isFirst = safeIndex === 0
  const isLast = safeIndex === steps.length - 1
  const progressPercent = steps.length > 0 ? ((safeIndex + 1) / steps.length) * 100 : 0

  if (!currentStep) return null

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>{currentStep.title}</SheetTitle>
          <SheetDescription>{currentStep.description}</SheetDescription>
        </SheetHeader>

        <div className="space-y-4 px-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {progressLabel}
          </p>
          <div className="h-2 rounded-full bg-muted">
            <div
              className="h-2 rounded-full bg-primary transition-all"
              style={{ width: `${Math.max(8, progressPercent)}%` }}
            />
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">
              {currentStep.description}
            </p>
            <Button
              type="button"
              variant="outline"
              className="mt-3"
              onClick={() => onNavigate(currentStep.href)}
              disabled={saving}
            >
              {currentStep.ctaLabel}
            </Button>
          </div>
        </div>

        <SheetFooter className="sm:flex-row sm:items-center sm:justify-between">
          <Button type="button" variant="ghost" onClick={onSkip} disabled={saving}>
            {skipLabel}
          </Button>
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" onClick={onPrevious} disabled={saving || isFirst}>
              {previousLabel}
            </Button>
            {isLast ? (
              <Button type="button" onClick={onFinish} disabled={saving}>
                {finishLabel}
              </Button>
            ) : (
              <Button type="button" onClick={onNext} disabled={saving}>
                {nextLabel}
              </Button>
            )}
          </div>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
