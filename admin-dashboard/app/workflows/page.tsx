"use client"

import * as React from "react"
import useSWR from "swr"
import { IconPlus, IconEdit, IconTrash } from "@tabler/icons-react"
import { toast } from "sonner"

import { AppShell } from "@/components/layout/app-shell"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { Badge } from "@/components/ui/badge"
import { requestApi, fetchApi } from "@/lib/api"

type WorkflowRule = {
  id: string
  name: string
  trigger_type: string
  criteria: Record<string, any>
  action_type: string
  action_config: Record<string, any>
  is_active: boolean
}

const fetcher = <T,>(path: string) => fetchApi<T>(path)

export default function WorkflowsPage() {
  const { data: workflows, error, isLoading, mutate } = useSWR<WorkflowRule[]>("/api/v1/admin/workflows", fetcher)
  
  const [open, setOpen] = React.useState(false)
  const [editingId, setEditingId] = React.useState<string | null>(null)
  const [isSaving, setIsSaving] = React.useState(false)
  
  const [formData, setFormData] = React.useState<Partial<WorkflowRule>>({
    name: "",
    trigger_type: "lead_scored",
    criteria: {},
    action_type: "create_task",
    action_config: {},
    is_active: true
  })

  const [criteriaMinScore, setCriteriaMinScore] = React.useState("80")
  const [actionTaskTitle, setActionTaskTitle] = React.useState("Follow up lead")

  React.useEffect(() => {
    if (!open) {
      setEditingId(null)
      setFormData({
        name: "",
        trigger_type: "lead_scored",
        criteria: {},
        action_type: "create_task",
        action_config: {},
        is_active: true
      })
      setCriteriaMinScore("80")
      setActionTaskTitle("Follow up lead")
    }
  }, [open])

  function handleEdit(rule: WorkflowRule) {
    setEditingId(rule.id)
    setFormData(rule)
    // Parse simplified state for UI
    setCriteriaMinScore(String(rule.criteria.min_score || "80"))
    setActionTaskTitle(rule.action_config.title || "Follow up lead")
    setOpen(true)
  }

  async function handleDelete(id: string) {
    if (!confirm("Supprimer ce workflow ?")) return
    try {
      await requestApi(`/api/v1/admin/workflows/${id}`, { method: "DELETE" })
      toast.success("Workflow supprimé")
      mutate()
    } catch {
      toast.error("Erreur suppression")
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsSaving(true)
    
    try {
      // Build payload
      const payload = {
        ...formData,
        criteria: { min_score: Number(criteriaMinScore) },
        action_config: { title: actionTaskTitle }
      }

      if (editingId) {
        await requestApi(`/api/v1/admin/workflows/${editingId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        })
        toast.success("Workflow mis à jour")
      } else {
        await requestApi("/api/v1/admin/workflows", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        })
        toast.success("Workflow créé")
      }
      setOpen(false)
      mutate()
    } catch (err) {
      toast.error("Erreur enregistrement")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <AppShell>
      <div className="flex items-center justify-between py-4">
        <h2 className="text-3xl font-bold tracking-tight">Workflows (Beta)</h2>
        <Button onClick={() => setOpen(true)}>
          <IconPlus className="mr-2 size-4" />
          Nouveau Workflow
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : error ? (
        <ErrorState title="Erreur chargement workflows" onRetry={() => mutate()} />
      ) : workflows?.length === 0 ? (
        <EmptyState 
          title="Aucun workflow" 
          description="Automatisez vos processus avec des règles simples."
          action={<Button onClick={() => setOpen(true)}>Créer mon premier workflow</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflows?.map(rule => (
            <Card key={rule.id}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{rule.name}</CardTitle>
                  <Badge variant={rule.is_active ? "default" : "secondary"}>
                    {rule.is_active ? "Actif" : "Inactif"}
                  </Badge>
                </div>
                <CardDescription>
                  Si {rule.trigger_type} alors {rule.action_type}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Critère: Score &gt; {rule.criteria.min_score}</p>
                  <p>Action: {rule.action_config.title}</p>
                </div>
                <div className="flex justify-end gap-2 mt-4 pt-4 border-t">
                  <Button variant="ghost" size="icon" onClick={() => handleEdit(rule)}>
                    <IconEdit className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="text-red-600" onClick={() => handleDelete(rule.id)}>
                    <IconTrash className="size-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>{editingId ? "Modifier Workflow" : "Nouveau Workflow"}</SheetTitle>
            <SheetDescription>Configurez vos règles d'automatisation.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleSubmit} className="space-y-6 py-6">
            <div className="space-y-2">
              <Label>Nom</Label>
              <Input 
                value={formData.name} 
                onChange={e => setFormData({...formData, name: e.target.value})} 
                placeholder="Ex: High Score Alert"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label>Trigger</Label>
              <Select 
                value={formData.trigger_type} 
                onValueChange={v => setFormData({...formData, trigger_type: v})}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="lead_scored">Lead Score Updated</SelectItem>
                  <SelectItem value="lead_created">Lead Created</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2 p-3 border rounded-md bg-muted/20">
              <Label>Conditions</Label>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-sm">Score min:</span>
                <Input 
                  type="number" 
                  value={criteriaMinScore} 
                  onChange={e => setCriteriaMinScore(e.target.value)}
                  className="w-20"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Action</Label>
              <Select 
                value={formData.action_type} 
                onValueChange={v => setFormData({...formData, action_type: v})}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="create_task">Créer une tâche</SelectItem>
                  <SelectItem value="change_status">Changer statut</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2 p-3 border rounded-md bg-muted/20">
              <Label>Configuration Action</Label>
              <div className="space-y-2 mt-2">
                <Label className="text-xs">Titre Tâche / Statut</Label>
                <Input 
                  value={actionTaskTitle} 
                  onChange={e => setActionTaskTitle(e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Switch 
                checked={formData.is_active} 
                onCheckedChange={c => setFormData({...formData, is_active: c})}
              />
              <Label>Activer ce workflow</Label>
            </div>

            <SheetFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSaving}>{isSaving ? "Enregistrement..." : "Enregistrer"}</Button>
            </SheetFooter>
          </form>
        </SheetContent>
      </Sheet>
    </AppShell>
  )
}
