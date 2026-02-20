"use client"

import * as React from "react"
import useSWR from "swr"
import { IconChartBar, IconCurrencyEuro, IconTarget, IconUsers } from "@tabler/icons-react"

import ChartAreaInteractive, { type TrendPoint } from "@/components/chart-area-interactive"
import RevenueForecastChart, { type ForecastPoint } from "@/components/revenue-forecast-chart"
import { AppShell } from "@/components/layout/app-shell"
import { SyncStatus } from "@/components/sync-status"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { Skeleton } from "@/components/ui/skeleton"
import { useLoadingTimeout } from "@/hooks/use-loading-timeout"
import { fetchApi } from "@/lib/api"
import { formatCurrencyFr, formatNumberFr } from "@/lib/format"
import { leadStatusLabel } from "@/lib/lead-status-labels"

type AnalyticsData = {
  total_leads: number
  leads_by_status: Record<string, number>
  task_completion_rate: number
  pipeline_value: number
  new_leads_today: number
}

type DashboardStats = {
  daily_pipeline_trend: TrendPoint[]
}

const fetcher = <T,>(path: string) => fetchApi<T>(path)

export default function AnalyticsPage() {
  const {
    data: analytics,
    error: analyticsError,
    isLoading: analyticsLoading,
    mutate: mutateAnalytics,
  } = useSWR<AnalyticsData>("/api/v1/admin/analytics", fetcher)
  const loadingTimedOut = useLoadingTimeout(analyticsLoading, 12_000)
  const { data: stats } = useSWR<DashboardStats>("/api/v1/admin/stats", fetcher)
  const { data: forecastData } = useSWR<{ forecast_monthly: ForecastPoint[] }>("/api/v1/admin/opportunities/forecast", fetcher)
  const [updatedAt, setUpdatedAt] = React.useState<Date | null>(null)

  React.useEffect(() => {
    if (!analytics) return
    setUpdatedAt(new Date())
  }, [analytics])

  const conversionRate = React.useMemo(() => {
    if (!analytics || analytics.total_leads === 0) return "0"
    const converted = analytics.leads_by_status["CONVERTED"] || 0
    return ((converted / analytics.total_leads) * 100).toFixed(1)
  }, [analytics])

  const statusRows = React.useMemo(
    () =>
      Object.entries(analytics?.leads_by_status || {}).sort((left, right) => right[1] - left[1]),
    [analytics?.leads_by_status],
  )

  return (
    <AppShell contentClassName="flex flex-1 flex-col p-0">
      <div className="flex flex-1 flex-col gap-4 p-3 pt-0 sm:p-4 sm:pt-0 lg:p-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Analytique</h1>
          <SyncStatus updatedAt={updatedAt} onRefresh={() => void mutateAnalytics()} />
        </div>

        {analyticsLoading && !loadingTimedOut ? (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Skeleton className="h-28 w-full" />
              <Skeleton className="h-28 w-full" />
              <Skeleton className="h-28 w-full" />
              <Skeleton className="h-28 w-full" />
            </div>
            <Skeleton className="h-80 w-full" />
          </div>
        ) : null}
        {!analyticsLoading && (analyticsError || loadingTimedOut) ? (
          <div role="alert" aria-live="assertive">
            <ErrorState
              title="Impossible de charger les données analytiques."
              description={
                loadingTimedOut
                  ? "Le chargement dépasse le délai attendu. Vérifiez la connectivité API puis relancez."
                  : analyticsError instanceof Error
                    ? analyticsError.message
                    : "Les données analytiques sont indisponibles."
              }
              secondaryLabel="Ouvrir Paramètres"
              secondaryHref="/settings"
              onRetry={() => void mutateAnalytics()}
            />
          </div>
        ) : null}
        {!analyticsLoading && !analyticsError && !loadingTimedOut && analytics && analytics.total_leads === 0 ? (
          <EmptyState
            title="Aucune donnée disponible"
            description="Les graphiques et KPI apparaîtront après création de vos premiers leads."
          />
        ) : null}
        {!analyticsLoading && !analyticsError && !loadingTimedOut && analytics && analytics.total_leads > 0 ? (
          <>
            <section aria-labelledby="analytics-kpi-heading">
              <h2 id="analytics-kpi-heading" className="sr-only">Indicateurs clés de performance</h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="rounded-xl border shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Valeur pipeline</CardTitle>
                    <IconCurrencyEuro className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrencyFr(analytics.pipeline_value)}</div>
                    <p className="text-xs text-muted-foreground">Estimation actuelle</p>
                  </CardContent>
                </Card>
                <Card className="rounded-xl border shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Taux de conversion</CardTitle>
                    <IconTarget className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{conversionRate}%</div>
                    <p className="text-xs text-muted-foreground">Leads convertis</p>
                  </CardContent>
                </Card>
                <Card className="rounded-xl border shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Complétion tâches</CardTitle>
                    <IconChartBar className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{Math.round(analytics.task_completion_rate)}%</div>
                    <p className="text-xs text-muted-foreground">Efficacité équipe</p>
                  </CardContent>
                </Card>
                <Card className="rounded-xl border shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Leads actifs</CardTitle>
                    <IconUsers className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatNumberFr(analytics.total_leads)}</div>
                    <p className="text-xs text-muted-foreground">
                      +{formatNumberFr(analytics.new_leads_today)} aujourd&apos;hui
                    </p>
                  </CardContent>
                </Card>
              </div>
            </section>

            <section aria-labelledby="analytics-charts-heading">
              <h2 id="analytics-charts-heading" className="sr-only">Graphiques et tendances</h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <div className="lg:col-span-4 space-y-4">
                  <ChartAreaInteractive trend={stats?.daily_pipeline_trend || []} />
                  <RevenueForecastChart data={forecastData?.forecast_monthly || []} />
                </div>
                <Card className="lg:col-span-3 rounded-xl border shadow-sm">
                  <CardHeader>
                    <CardTitle>Leads par statut</CardTitle>
                    <CardDescription>Distribution par étape pipeline</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4" role="img" aria-label={`Distribution des ${analytics.total_leads} leads par statut`}>
                      {statusRows.map(([status, count]) => (
                        <div key={status} className="flex items-center">
                          <div className="w-full">
                            <div className="flex items-center justify-between text-sm">
                              <span>{leadStatusLabel(status)}</span>
                              <span className="font-semibold">
                                {formatNumberFr(count)} (
                                {Math.round((count / Math.max(analytics.total_leads, 1)) * 100)}%)
                              </span>
                            </div>
                            <div className="mt-1 h-2 w-full rounded-full bg-secondary" aria-hidden="true">
                              <div
                                className="h-full rounded-full bg-primary"
                                style={{
                                  width: `${(count / Math.max(analytics.total_leads, 1)) * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  )
}




