"use client"

import * as React from "react"
import useSWR from "swr"
import { IconRocket, IconPlus, IconTrash, IconCircleCheck, IconSettings } from "@tabler/icons-react"
import { toast } from "sonner"

import { AppShell } from "@/components/layout/app-shell"
import { SyncStatus } from "@/components/sync-status"
import { EmptyState } from "@/components/ui/empty-state"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { fetchApi, requestApi } from "@/lib/api"

type WorkflowRule = {
  id: string
  name: string
  trigger_type: string
  criteria: Record<string, any>
  action_type: string
  action_config: Record<string, any>
  is_active: bool
}

const fetcher = <T,>(path: string) => fetchApi<T>(path)

export default function WorkflowsPage() {
  const { data: workflows, isLoading, mutate } = useSWR<WorkflowRule[]>("/api/v1/admin/workflows", fetcher)
  const [busy, setBusy] = React.useState(false)

  // Quick Create State
  const [name, setName] = React.useState("")
  const [minScore, setMinScore] = React.useState("80")

  async function createDefaultWorkflow() {
    if (!name.trim()) {
      toast.error("Veuillez donner un nom à l'automatisation.")
      return
    }
    setBusy(true)
    try {
      await requestApi("/api/v1/admin/workflows", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          trigger_type: "lead_scored",
          criteria: { min_score: parseInt(minScore, 10) },
          action_type: "create_task",
          action_config: { title: "Relance manuelle: Lead chaud détecté", priority: "High" },
          is_active: true
        })
      })
      toast.success("Automatisation créée !")
      setName("")
      await mutate()
    } catch (error) {
      toast.error("Erreur lors de la création.")
    } finally {
      setBusy(false)
    }
  }

  async function deleteWorkflow(id: string) {
    try {
      await requestApi(`/api/v1/admin/workflows/${id}`, { method: "DELETE" })
      toast.success("Automatisation supprimée.")
      await mutate()
    } catch {
      toast.error("Erreur lors de la suppression.")
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Automatisations (Workflows)</h2>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_400px]">
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <IconRocket className="h-5 w-5 text-primary" />
            Règles actives
          </h3>

          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : (workflows || []).length === 0 ? (
            <EmptyState 
              title="Aucune automatisation" 
              description="Créez votre première règle pour automatiser votre pipeline."
            />
          ) : (
            workflows?.map(rule => (
              <Card key={rule.id}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="font-bold">{rule.name}</p>
                      <Badge variant="secondary">Active</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Trigger: <span className="text-foreground">{rule.trigger_type}</span> | 
                      Action: <span className="text-foreground">{rule.action_type}</span>
                    </p>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => deleteWorkflow(rule.id)}>
                    <IconTrash className="h-4 w-4 text-destructive" />
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Nouvelle règle rapide</CardTitle>
              <CardDescription>Configurez une règle de score automatiquement.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Nom de la règle</Label>
                <Input 
                  value={name} 
                  onChange={(e) => setName(e.target.value)} 
                  placeholder="Ex: Alerte Lead Chaud"
                />
              </div>
              <div className="space-y-2">
                <Label>Score minimum requis</Label>
                <Input 
                  type="number" 
                  value={minScore} 
                  onChange={(e) => setMinScore(e.target.value)} 
                />
              </div>
              <div className="p-3 bg-accent/50 rounded-md text-xs space-y-2">
                <p className="font-semibold flex items-center gap-1">
                  <IconSettings className="h-3 w-3" /> Action configurée :
                </p>
                <p>Créer une tâche "Relance manuelle" (Priorité Haute) assignée à Vous.</p>
              </div>
              <Button className="w-full" onClick={createDefaultWorkflow} disabled={busy}>
                {busy ? "Création..." : "Créer l'automatisation"}
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-primary/5 border-primary/20">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <IconCircleCheck className="h-4 w-4 text-primary" />
                Automatisations Système
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-3">
              <p>• Passage en <b>BOOKED</b> auto lors d&apos;un RDV.</p>
              <p>• Calcul du score ICP lors du sourcing.</p>
              <p>• Génération d&apos;accroche personnalisée.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  )
}
