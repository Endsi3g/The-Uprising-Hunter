"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type ResponsiveDataViewProps = {
  mobileCards: React.ReactNode
  desktopTable: React.ReactNode
  className?: string
}

export function ResponsiveDataView({
  mobileCards,
  desktopTable,
  className,
}: ResponsiveDataViewProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="space-y-3 md:hidden">{mobileCards}</div>
      <div className="hidden md:block">{desktopTable}</div>
    </div>
  )
}
