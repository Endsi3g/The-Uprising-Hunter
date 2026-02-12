"use client"

import * as React from "react"
import { IconDotsVertical, IconFolderPlus, IconPlus, IconRocket } from "@tabler/icons-react"
import { toast } from "sonner"

import { useModalSystem } from "@/components/modal-system-provider"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { requestApi } from "@/lib/api"

export type Lead = {
  id: string
  name: string
  company: {
    name: string
  }
  email: string
  phone: string
  status: string
  score: number
  segment: string
}

function scoreClass(score: number): string {
  if (score >= 80) return "text-green-600"
  if (score >= 50) return "text-orange-600"
  return "text-muted-foreground"
}

export function LeadsTable({
  data,
  onDataChanged,
}: {
  data: Lead[]
  onDataChanged?: () => void
}) {
  const { openProjectForm } = useModalSystem()
  const [filter, setFilter] = React.useState("")

  const filteredData = React.useMemo(() => {
    const cleanFilter = filter.trim().toLowerCase()
    if (!cleanFilter) return data
    return data.filter((lead) => {
      return (
        lead.name.toLowerCase().includes(cleanFilter) ||
        lead.email.toLowerCase().includes(cleanFilter) ||
        lead.company.name.toLowerCase().includes(cleanFilter) ||
        lead.segment.toLowerCase().includes(cleanFilter)
      )
    })
  }, [data, filter])

  async function createTaskFromLead(lead: Lead) {
    const payload = {
      title: `Suivi lead - ${lead.name}`,
      status: "To Do",
      priority: "Medium",
      assigned_to: "Vous",
      lead_id: lead.id,
    }
    try {
      await requestApi("/api/v1/admin/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      toast.success("Tache creee depuis le lead.")
      onDataChanged?.()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Creation de tache impossible")
    }
  }

  function createProjectFromLead(lead: Lead) {
    openProjectForm({
      mode: "create",
      project: {
        name: `Projet - ${lead.company.name}`,
        description: `Projet cree depuis le lead ${lead.name}`,
        status: "Planning",
        lead_id: lead.id,
      },
      onSuccess: () => {
        toast.success("Projet cree depuis le lead.")
        onDataChanged?.()
      },
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <Input
          placeholder="Filtrer les leads..."
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          className="sm:max-w-md"
        />
        <p className="text-sm text-muted-foreground">{filteredData.length} lead(s)</p>
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Lead</TableHead>
              <TableHead>Entreprise</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Segment</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.map((lead) => (
              <TableRow key={lead.id}>
                <TableCell>
                  <div className="font-medium">{lead.name}</div>
                  <div className="text-xs text-muted-foreground">{lead.email}</div>
                </TableCell>
                <TableCell>{lead.company.name}</TableCell>
                <TableCell>
                  <Badge variant="outline">{lead.status}</Badge>
                </TableCell>
                <TableCell>
                  <span className={`font-semibold ${scoreClass(lead.score)}`}>{lead.score}</span>
                </TableCell>
                <TableCell>{lead.segment}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="size-8">
                        <IconDotsVertical className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <DropdownMenuItem onClick={() => createProjectFromLead(lead)}>
                        <IconFolderPlus className="size-4" />
                        Creer un projet
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => createTaskFromLead(lead)}>
                        <IconPlus className="size-4" />
                        Creer une tache
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => toast.info("Flow audit disponible prochainement")}> 
                        <IconRocket className="size-4" />
                        Generer un audit
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
            {filteredData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
                  Aucun lead ne correspond a votre recherche.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
