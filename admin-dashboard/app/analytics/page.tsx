"use client"

import * as React from "react"
import useSWR from "swr"
import { IconChartBar, IconCurrencyEuro, IconTarget, IconUsers } from "@tabler/icons-react"

import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchApi } from "@/lib/api"
import { formatCurrencyFr, formatNumberFr } from "@/lib/format"

type AnalyticsData = {
  total_leads: number
  leads_by_status: Record<string, number>
  task_completion_rate: number
  pipeline_value: number
  new_leads_today: number
}

const fetcher = <T,>(path: string) => fetchApi<T>(path)

export default function AnalyticsPage() {
  const { data: stats, error, isLoading } = useSWR<AnalyticsData>("/api/v1/admin/analytics", fetcher)

  const conversionRate = React.useMemo(() => {
    if (!stats || stats.total_leads === 0) return "0.0"
    const converted = stats.leads_by_status["CONVERTED"] || 0
    return ((converted / stats.total_leads) * 100).toFixed(1)
  }, [stats])

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
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0 md:p-8">
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-bold tracking-tight">Analytique</h2>
          </div>

          {isLoading ? (
            <div>Chargement des statistiques...</div>
          ) : error ? (
            <div className="text-red-500 text-sm">Impossible de charger les donnees analytiques.</div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card className="rounded-xl border shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Valeur pipeline</CardTitle>
                  <IconCurrencyEuro className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatCurrencyFr(stats?.pipeline_value)}</div>
                  <p className="text-xs text-muted-foreground">Estimation actuelle</p>
                </CardContent>
              </Card>
              <Card className="rounded-xl border shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Conversion leads</CardTitle>
                  <IconTarget className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{conversionRate}%</div>
                  <p className="text-xs text-muted-foreground">Leads convertis</p>
                </CardContent>
              </Card>
              <Card className="rounded-xl border shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Completion taches</CardTitle>
                  <IconChartBar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{Math.round(stats?.task_completion_rate || 0)}%</div>
                  <p className="text-xs text-muted-foreground">Efficacite equipe</p>
                </CardContent>
              </Card>
              <Card className="rounded-xl border shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Leads actifs</CardTitle>
                  <IconUsers className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatNumberFr(stats?.total_leads)}</div>
                  <p className="text-xs text-muted-foreground">
                    +{formatNumberFr(stats?.new_leads_today)} aujourd'hui
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4 rounded-xl border shadow-sm">
              <CardHeader>
                <CardTitle>Vue globale</CardTitle>
                <CardDescription>Volume des leads et activite commerciale</CardDescription>
              </CardHeader>
              <CardContent className="pl-2">
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Graphique de volume disponible depuis le tableau de bord principal.
                </div>
              </CardContent>
            </Card>
            <Card className="col-span-3 rounded-xl border shadow-sm">
              <CardHeader>
                <CardTitle>Leads par statut</CardTitle>
                <CardDescription>Distribution par etape pipeline</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {stats?.leads_by_status &&
                    Object.entries(stats.leads_by_status).map(([status, count]) => (
                      <div key={status} className="flex items-center">
                        <div className="w-full">
                          <div className="flex items-center justify-between text-sm">
                            <span>{status}</span>
                            <span className="font-semibold">{formatNumberFr(count)}</span>
                          </div>
                          <div className="mt-1 h-2 w-full rounded-full bg-secondary">
                            <div
                              className="h-full rounded-full bg-primary"
                              style={{ width: `${(count / Math.max(stats.total_leads, 1)) * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

