"use client"

import * as React from "react"

import { AppSidebar } from "@/components/app-sidebar"
import { AssistantProspectPanel } from "@/components/assistant-prospect-panel"
import { SiteHeader } from "@/components/site-header"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"

export default function AssistantPage() {
  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col gap-4 p-3 pt-0 sm:p-4 sm:pt-0 lg:p-6">
          <h2 className="text-3xl font-bold tracking-tight">Assistant</h2>
          <AssistantProspectPanel />
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

