"use client"

import * as React from "react"
import useSWR from "swr"
import { toast } from "sonner"

import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { requestApi } from "@/lib/api"

type SettingsPayload = {
  organization_name: string
  locale: string
  timezone: string
  default_page_size: number
  dashboard_refresh_seconds: number
  support_email: string
}

const fetcher = <T,>(path: string) => requestApi<T>(path)

export default function SettingsPage() {
  const { data, error, isLoading, mutate } = useSWR<SettingsPayload>(
    "/api/v1/admin/settings",
    fetcher,
  )
  const [isSaving, setIsSaving] = React.useState(false)
  const [form, setForm] = React.useState<SettingsPayload>({
    organization_name: "",
    locale: "fr-FR",
    timezone: "Europe/Paris",
    default_page_size: 25,
    dashboard_refresh_seconds: 30,
    support_email: "",
  })

  React.useEffect(() => {
    if (!data) return
    setForm(data)
  }, [data])

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setIsSaving(true)
      await requestApi("/api/v1/admin/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      })
      toast.success("Parametres enregistres.")
      await mutate()
    } catch (submitError) {
      toast.error(submitError instanceof Error ? submitError.message : "Echec de sauvegarde")
    } finally {
      setIsSaving(false)
    }
  }

  function updateField<K extends keyof SettingsPayload>(key: K, value: SettingsPayload[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

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
          <h2 className="text-3xl font-bold tracking-tight">Parametres</h2>
          {error ? (
            <div className="text-sm text-red-600">Impossible de charger les parametres.</div>
          ) : null}
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            <form onSubmit={onSubmit} className="max-w-3xl space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="organization_name">Organisation</Label>
                  <Input
                    id="organization_name"
                    value={form.organization_name}
                    onChange={(event) => updateField("organization_name", event.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="support_email">Email support</Label>
                  <Input
                    id="support_email"
                    type="email"
                    value={form.support_email}
                    onChange={(event) => updateField("support_email", event.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="locale">Locale</Label>
                  <Input
                    id="locale"
                    value={form.locale}
                    onChange={(event) => updateField("locale", event.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Fuseau horaire</Label>
                  <Input
                    id="timezone"
                    value={form.timezone}
                    onChange={(event) => updateField("timezone", event.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="default_page_size">Taille de page par defaut</Label>
                  <Input
                    id="default_page_size"
                    type="number"
                    min={5}
                    max={200}
                    value={form.default_page_size}
                    onChange={(event) => updateField("default_page_size", Number(event.target.value))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dashboard_refresh_seconds">Refresh dashboard (s)</Label>
                  <Input
                    id="dashboard_refresh_seconds"
                    type="number"
                    min={10}
                    max={3600}
                    value={form.dashboard_refresh_seconds}
                    onChange={(event) => updateField("dashboard_refresh_seconds", Number(event.target.value))}
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? "Enregistrement..." : "Enregistrer"}
                </Button>
              </div>
            </form>
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
