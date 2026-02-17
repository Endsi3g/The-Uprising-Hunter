"use client"

import * as React from "react"
import useSWR from "swr"
import { toast } from "sonner"

import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { useLoadingTimeout } from "@/hooks/use-loading-timeout"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { requestApi } from "@/lib/api"
import { formatDateTimeFr, formatNumberFr } from "@/lib/format"

type Role = {
  id: number
  key: string
  label: string
}

type User = {
  id: string
  email: string
  display_name?: string | null
  status: "active" | "invited" | "disabled"
  roles: string[]
}

type UsersResponse = {
  items: User[]
}

type RolesResponse = {
  items: Role[]
}

type WorkloadOwner = {
  user_id: string
  email: string
  display_name: string
  status: string
  lead_count_total: number
  lead_count_active: number
  overdue_sla_count: number
}

type WorkloadResponse = {
  generated_at: string
  items: WorkloadOwner[]
  unassigned_active_leads: number
}

type FunnelConfig = {
  stages: string[]
  terminal_stages: string[]
  stage_sla_hours: Record<string, number>
  next_action_hours: Record<string, number>
  model: string
}

type ConversionFunnelResponse = {
  window_days: number
  from: string
  to: string
  items: Array<{
    stage: string
    lead_count: number
    entries_in_window: number
    conversion_from_previous_percent: number
  }>
  totals: {
    won: number
    post_sale: number
    lost: number
    disqualified: number
  }
}

type Recommendation = {
  id: string
  entity_type: string
  entity_id: string
  recommendation_type: string
  priority: number
  payload: Record<string, unknown>
  status: string
  requires_confirm: boolean
  created_at?: string | null
}

type RecommendationsResponse = {
  total: number
  items: Recommendation[]
}

const USER_STATUSES: User["status"][] = ["active", "invited", "disabled"]
const fetcher = <T,>(path: string) => requestApi<T>(path)

function userLabel(user: User): string {
  return (user.display_name || "").trim() || user.email
}

function recommendationTitle(item: Recommendation): string {
  const payloadTitle = item.payload?.title
  if (typeof payloadTitle === "string" && payloadTitle.trim()) return payloadTitle
  return item.recommendation_type.replaceAll("_", " ")
}

function toNonNegativeInt(value: string, fallback: number): number {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return fallback
  return Math.max(0, Math.round(parsed))
}

export default function TeamSettingsPage() {
  const { data: usersData, error: usersError, isLoading: usersLoading, mutate: mutateUsers } = useSWR<UsersResponse>(
    "/api/v1/admin/users",
    fetcher,
  )
  const { data: rolesData, error: rolesError, isLoading: rolesLoading, mutate: mutateRoles } = useSWR<RolesResponse>(
    "/api/v1/admin/roles",
    fetcher,
  )
  const { data: workloadData, error: workloadError, isLoading: workloadLoading, mutate: mutateWorkload } = useSWR<WorkloadResponse>(
    "/api/v1/admin/workload/owners",
    fetcher,
  )
  const { data: funnelConfigData, error: funnelError, isLoading: funnelLoading, mutate: mutateFunnelConfig } = useSWR<FunnelConfig>(
    "/api/v1/admin/funnel/config",
    fetcher,
  )
  const { data: conversionData, error: conversionError, isLoading: conversionLoading, mutate: mutateConversion } = useSWR<ConversionFunnelResponse>(
    "/api/v1/admin/conversion/funnel?days=30",
    fetcher,
  )
  const { data: recommendationsData, error: recommendationsError, isLoading: recommendationsLoading, mutate: mutateRecommendations } = useSWR<RecommendationsResponse>(
    "/api/v1/admin/recommendations?status=pending&limit=100&offset=0&seed=true",
    fetcher,
  )

  const loadingTimedOut = useLoadingTimeout(usersLoading || rolesLoading, 12_000)

  const [email, setEmail] = React.useState("")
  const [displayName, setDisplayName] = React.useState("")
  const [inviteRole, setInviteRole] = React.useState("sales")
  const [submitting, setSubmitting] = React.useState(false)
  const [updatingId, setUpdatingId] = React.useState<string | null>(null)
  const [pendingStatus, setPendingStatus] = React.useState<Record<string, User["status"]>>({})
  const [pendingRole, setPendingRole] = React.useState<Record<string, string>>({})

  const [configDraft, setConfigDraft] = React.useState<FunnelConfig | null>(null)
  const [savingConfig, setSavingConfig] = React.useState(false)

  const [recommendationBusyId, setRecommendationBusyId] = React.useState<string | null>(null)

  const [taskIdsRaw, setTaskIdsRaw] = React.useState("")
  const [bulkAssignedTo, setBulkAssignedTo] = React.useState("")
  const [bulkAssignBusy, setBulkAssignBusy] = React.useState(false)

  const roleOptions = React.useMemo(() => rolesData?.items || [], [rolesData])
  const users = React.useMemo(() => usersData?.items || [], [usersData])
  const recommendations = React.useMemo(() => recommendationsData?.items || [], [recommendationsData])

  const workflowLoading = workloadLoading || funnelLoading || conversionLoading || recommendationsLoading
  const workflowError = workloadError || funnelError || conversionError || recommendationsError

  const configStages = React.useMemo(() => {
    const keys = new Set<string>()
    for (const stage of configDraft?.stages || []) keys.add(stage)
    for (const key of Object.keys(configDraft?.stage_sla_hours || {})) keys.add(key)
    for (const key of Object.keys(configDraft?.next_action_hours || {})) keys.add(key)
    return Array.from(keys)
  }, [configDraft])

  React.useEffect(() => {
    if (roleOptions.length > 0 && !roleOptions.some((role) => role.key === inviteRole)) {
      setInviteRole(roleOptions[0].key)
    }
  }, [inviteRole, roleOptions])

  React.useEffect(() => {
    if (funnelConfigData) {
      setConfigDraft(funnelConfigData)
    }
  }, [funnelConfigData])

  React.useEffect(() => {
    if (!bulkAssignedTo && users.length > 0) {
      setBulkAssignedTo(userLabel(users[0]))
    }
  }, [bulkAssignedTo, users])

  async function inviteUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setSubmitting(true)
      await requestApi("/api/v1/admin/users/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          display_name: displayName || null,
          roles: [inviteRole],
        }),
      })
      toast.success("Invitation envoyee.")
      setEmail("")
      setDisplayName("")
      await mutateUsers()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Invitation impossible")
    } finally {
      setSubmitting(false)
    }
  }

  async function updateUser(user: User) {
    const status = pendingStatus[user.id] || user.status
    const role = pendingRole[user.id] || user.roles[0] || "sales"
    try {
      setUpdatingId(user.id)
      await requestApi(`/api/v1/admin/users/${user.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status,
          roles: [role],
        }),
      })
      toast.success("Utilisateur mis a jour.")
      await mutateUsers()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Mise a jour impossible")
    } finally {
      setUpdatingId(null)
    }
  }

  function updateDraftHour(
    kind: "stage_sla_hours" | "next_action_hours",
    stage: string,
    value: string,
  ) {
    setConfigDraft((current) => {
      if (!current) return current
      const currentValue = current[kind][stage] ?? 0
      return {
        ...current,
        [kind]: {
          ...current[kind],
          [stage]: toNonNegativeInt(value, currentValue),
        },
      }
    })
  }

  async function saveFunnelConfig() {
    if (!configDraft) return
    try {
      setSavingConfig(true)
      await requestApi("/api/v1/admin/funnel/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stages: configDraft.stages,
          terminal_stages: configDraft.terminal_stages,
          stage_sla_hours: configDraft.stage_sla_hours,
          next_action_hours: configDraft.next_action_hours,
          model: configDraft.model,
        }),
      })
      toast.success("Configuration funnel sauvegardee.")
      await Promise.all([mutateFunnelConfig(), mutateConversion()])
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Sauvegarde impossible")
    } finally {
      setSavingConfig(false)
    }
  }

  async function applyRecommendation(id: string) {
    try {
      setRecommendationBusyId(id)
      await requestApi(`/api/v1/admin/recommendations/${id}/apply`, { method: "POST" })
      toast.success("Recommandation appliquee.")
      await Promise.all([mutateRecommendations(), mutateWorkload(), mutateConversion()])
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Application impossible")
    } finally {
      setRecommendationBusyId(null)
    }
  }

  async function dismissRecommendation(id: string) {
    try {
      setRecommendationBusyId(id)
      await requestApi(`/api/v1/admin/recommendations/${id}/dismiss`, { method: "POST" })
      toast.success("Recommandation ignoree.")
      await mutateRecommendations()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Action impossible")
    } finally {
      setRecommendationBusyId(null)
    }
  }

  async function bulkAssignTasks() {
    const taskIds = taskIdsRaw
      .split(/[\n,;\s]+/)
      .map((item) => item.trim())
      .filter(Boolean)
    if (taskIds.length === 0) return toast.error("Renseignez au moins un task_id.")
    if (!bulkAssignedTo.trim()) return toast.error("Selectionnez un assignee.")
    try {
      setBulkAssignBusy(true)
      const result = await requestApi<{ updated: number; requested: number; assigned_to: string }>("/api/v1/admin/tasks/bulk-assign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_ids: taskIds,
          assigned_to: bulkAssignedTo.trim(),
          reason: "team_settings_bulk_assign",
        }),
      })
      toast.success(`${result.updated}/${result.requested} taches assignees a ${result.assigned_to}.`)
      await mutateWorkload()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Assignation impossible")
    } finally {
      setBulkAssignBusy(false)
    }
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
        <div className="flex flex-1 flex-col gap-4 p-3 pt-0 sm:p-4 sm:pt-0 lg:p-6">
          <h2 className="text-3xl font-bold tracking-tight">Equipe, ownership & funnel</h2>

          <Card>
            <CardHeader>
              <CardTitle>Inviter un utilisateur</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={inviteUser} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="space-y-2 lg:col-span-2">
                  <Label htmlFor="invite-email">Email</Label>
                  <Input
                    id="invite-email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-name">Nom</Label>
                  <Input
                    id="invite-name"
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select value={inviteRole} onValueChange={setInviteRole}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {roleOptions.map((role) => (
                        <SelectItem key={role.key} value={role.key}>
                          {role.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="sm:col-span-2 lg:col-span-4">
                  <Button type="submit" disabled={submitting}>
                    {submitting ? "Invitation..." : "Inviter"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {(usersLoading || rolesLoading) && !loadingTimedOut ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : null}
          {(!usersLoading && (usersError || rolesError)) || loadingTimedOut ? (
            <ErrorState
              title="Impossible de charger les membres de l'equipe."
              description={
                loadingTimedOut
                  ? "Le chargement est trop long. Vérifiez la disponibilite de l'API utilisateurs."
                  : usersError instanceof Error
                    ? usersError.message
                    : rolesError instanceof Error
                      ? rolesError.message
                      : "Les informations equipe/roles sont indisponibles."
              }
              secondaryLabel="Retour Parametres"
              secondaryHref="/settings"
              onRetry={() => {
                void mutateUsers()
                void mutateRoles()
              }}
            />
          ) : null}
          {!usersLoading && !usersError && !loadingTimedOut && users.length === 0 ? (
            <EmptyState
              title="Aucun membre pour le moment"
              description="Invitez votre equipe pour activer la gestion des roles et permissions."
            />
          ) : null}
          {!usersLoading && !usersError && !loadingTimedOut && users.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Utilisateurs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="grid gap-3 rounded-lg border p-3 sm:grid-cols-2 lg:grid-cols-6 lg:items-center"
                  >
                    <div className="lg:col-span-2">
                      <p className="text-sm font-medium">{userLabel(user)}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                    <div>
                      <Select
                        value={pendingStatus[user.id] || user.status}
                        onValueChange={(value) =>
                          setPendingStatus((current) => ({
                            ...current,
                            [user.id]: value as User["status"],
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {USER_STATUSES.map((statusValue) => (
                            <SelectItem key={statusValue} value={statusValue}>
                              {statusValue}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Select
                        value={pendingRole[user.id] || user.roles[0] || "sales"}
                        onValueChange={(value) =>
                          setPendingRole((current) => ({ ...current, [user.id]: value }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {roleOptions.map((role) => (
                            <SelectItem key={role.key} value={role.key}>
                              {role.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="lg:col-span-2">
                      <Button
                        variant="outline"
                        onClick={() => void updateUser(user)}
                        disabled={updatingId === user.id}
                      >
                        {updatingId === user.id ? "Mise a jour..." : "Enregistrer"}
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : null}

          {workflowLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : null}

          {!workflowLoading && workflowError ? (
            <ErrorState
              title="Impossible de charger le workflow funnel."
              description={workflowError instanceof Error ? workflowError.message : "Donnees funnel indisponibles."}
              onRetry={() => {
                void mutateWorkload()
                void mutateFunnelConfig()
                void mutateConversion()
                void mutateRecommendations()
              }}
            />
          ) : null}

          {!workflowLoading && !workflowError ? (
            <div className="grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Workload owners</CardTitle>
                  <CardDescription>
                    Snapshot: {formatDateTimeFr(workloadData?.generated_at || null)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="rounded-lg border p-3">
                    <p className="text-sm">
                      Leads actifs non assignes: <span className="font-medium">{workloadData?.unassigned_active_leads || 0}</span>
                    </p>
                  </div>
                  {(workloadData?.items || []).map((owner) => (
                    <div key={owner.user_id} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium">{owner.display_name}</p>
                        <Badge variant={owner.overdue_sla_count > 0 ? "destructive" : "outline"}>
                          SLA overdue {owner.overdue_sla_count}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{owner.email}</p>
                      <div className="mt-2 flex gap-4 text-xs">
                        <span>Total: {owner.lead_count_total}</span>
                        <span>Actifs: {owner.lead_count_active}</span>
                        <span>Status: {owner.status}</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Conversion funnel ({conversionData?.window_days || 30} jours)</CardTitle>
                  <CardDescription>
                    Fenetre: {formatDateTimeFr(conversionData?.from || null)} {"->"} {formatDateTimeFr(conversionData?.to || null)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {(conversionData?.items || []).map((item) => (
                    <div key={item.stage} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium">{item.stage}</p>
                        <Badge variant="outline">{item.lead_count} leads</Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Entries: {item.entries_in_window} | Conv. prev: {formatNumberFr(item.conversion_from_previous_percent)}%
                      </p>
                    </div>
                  ))}
                  <div className="grid gap-2 sm:grid-cols-2">
                    <div className="rounded-lg border p-2 text-xs">Won: {conversionData?.totals.won || 0}</div>
                    <div className="rounded-lg border p-2 text-xs">Post-sale: {conversionData?.totals.post_sale || 0}</div>
                    <div className="rounded-lg border p-2 text-xs">Lost: {conversionData?.totals.lost || 0}</div>
                    <div className="rounded-lg border p-2 text-xs">Disqualified: {conversionData?.totals.disqualified || 0}</div>
                  </div>
                </CardContent>
              </Card>

              <Card className="xl:col-span-2">
                <CardHeader>
                  <CardTitle>Configuration funnel</CardTitle>
                  <CardDescription>Reglez SLA et next action par etape.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {configDraft ? (
                    <>
                      <div className="grid gap-3 sm:grid-cols-3">
                        <div className="space-y-1 sm:col-span-1">
                          <Label>Model</Label>
                          <Input
                            value={configDraft.model || "canonical_v1"}
                            onChange={(event) =>
                              setConfigDraft((current) =>
                                current ? { ...current, model: event.target.value } : current,
                              )
                            }
                          />
                        </div>
                        <div className="space-y-1 sm:col-span-2">
                          <Label>Terminal stages</Label>
                          <Input
                            value={(configDraft.terminal_stages || []).join(", ")}
                            onChange={(event) =>
                              setConfigDraft((current) =>
                                current
                                  ? {
                                    ...current,
                                    terminal_stages: event.target.value
                                      .split(",")
                                      .map((item) => item.trim())
                                      .filter(Boolean),
                                  }
                                  : current,
                              )
                            }
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        {configStages.map((stage) => (
                          <div key={stage} className="grid gap-2 rounded-lg border p-3 sm:grid-cols-3 sm:items-center">
                            <p className="text-sm font-medium">{stage}</p>
                            <div className="space-y-1">
                              <Label className="text-xs">SLA (h)</Label>
                              <Input
                                type="number"
                                min={0}
                                value={String(configDraft.stage_sla_hours[stage] ?? 0)}
                                onChange={(event) => updateDraftHour("stage_sla_hours", stage, event.target.value)}
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs">Next action (h)</Label>
                              <Input
                                type="number"
                                min={0}
                                value={String(configDraft.next_action_hours[stage] ?? 0)}
                                onChange={(event) => updateDraftHour("next_action_hours", stage, event.target.value)}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                      <Button onClick={() => void saveFunnelConfig()} disabled={savingConfig}>
                        {savingConfig ? "Sauvegarde..." : "Sauvegarder config funnel"}
                      </Button>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">Aucune configuration disponible.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recommandations intelligentes</CardTitle>
                  <CardDescription>Actions IA en attente.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {recommendations.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Aucune recommandation pending.</p>
                  ) : (
                    recommendations.map((item) => (
                      <div key={item.id} className="rounded-lg border p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-medium">{recommendationTitle(item)}</p>
                          <Badge variant="outline">P{item.priority}</Badge>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {item.entity_type}:{" "}{item.entity_id} | {formatDateTimeFr(item.created_at || null)}
                        </p>
                        <div className="mt-2 flex gap-2">
                          <Button
                            size="sm"
                            disabled={recommendationBusyId === item.id}
                            onClick={() => void applyRecommendation(item.id)}
                          >
                            {recommendationBusyId === item.id ? "..." : "Appliquer"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={recommendationBusyId === item.id}
                            onClick={() => void dismissRecommendation(item.id)}
                          >
                            Ignorer
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Assignation massive taches</CardTitle>
                  <CardDescription>Utilise l&apos;endpoint tasks/bulk-assign.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <Label>Task IDs (separes par virgules, espaces ou sauts de ligne)</Label>
                    <Input
                      value={taskIdsRaw}
                      onChange={(event) => setTaskIdsRaw(event.target.value)}
                      placeholder="task-001, task-002, task-003"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Assigner a</Label>
                    <Select value={bulkAssignedTo} onValueChange={setBulkAssignedTo}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {users.map((user) => (
                          <SelectItem key={user.id} value={userLabel(user)}>
                            {userLabel(user)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button disabled={bulkAssignBusy} onClick={() => void bulkAssignTasks()}>
                    {bulkAssignBusy ? "Assignation..." : "Assigner les taches"}
                  </Button>
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

