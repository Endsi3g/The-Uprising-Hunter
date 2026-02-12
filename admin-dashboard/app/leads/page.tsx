"use client"

import * as React from "react"
import useSWR from "swr"

import { AppSidebar } from "@/components/app-sidebar"
import { Lead, LeadsTable } from "@/components/leads-table"
import { SiteHeader } from "@/components/site-header"
import { fetchApi } from "@/lib/api"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"

type ApiLead = {
  id: string
  email: string
  first_name?: string
  last_name?: string
  company_name?: string | null
  status: string
  segment?: string | null
  total_score?: number
}

type LeadsResponse = {
  page: number
  page_size: number
  total: number
  items: ApiLead[]
}

const fetcher = <T,>(path: string) => fetchApi<T>(path)

export default function LeadsPage() {
  const { data, error, isLoading, mutate } = useSWR<LeadsResponse>(
    "/api/v1/admin/leads?page=1&page_size=100",
    fetcher,
  )

  React.useEffect(() => {
    const handler = () => {
      void mutate()
    }
    window.addEventListener("prospect:lead-created", handler)
    return () => window.removeEventListener("prospect:lead-created", handler)
  }, [mutate])

  const leads: Lead[] = data?.items
    ? data.items.map((item) => ({
      id: item.id,
      name: `${item.first_name || ""} ${item.last_name || ""}`.trim() || item.email,
      company: { name: item.company_name || "Inconnu" },
      email: item.email,
      phone: "",
      status: item.status,
      score: Number(item.total_score || 0),
      segment: item.segment || "General",
    }))
    : []

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
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          <div className="flex items-center justify-between py-4">
            <h2 className="text-3xl font-bold tracking-tight">Leads</h2>
          </div>
          {error ? (
            <div className="text-sm text-red-600">
              Erreur de chargement des leads.
            </div>
          ) : null}
          {isLoading ? (
            <div>Chargement des leads...</div>
          ) : (
            <LeadsTable data={leads} onDataChanged={() => void mutate()} />
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

