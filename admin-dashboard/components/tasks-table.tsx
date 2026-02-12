"use client"

import * as React from "react"
import { IconDotsVertical, IconFolderUp, IconPencil, IconTrash } from "@tabler/icons-react"
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
import { formatDateFr } from "@/lib/format"

export type Task = {
  id: string
  title: string
  status: "To Do" | "In Progress" | "Done"
  priority: "Low" | "Medium" | "High" | "Critical"
  due_date: string
  assigned_to: string
  lead_id?: string
}

function priorityClass(priority: Task["priority"]): string {
  if (priority === "Critical") return "border-red-500 text-red-600"
  if (priority === "High") return "border-orange-500 text-orange-600"
  return ""
}

export function TasksTable({
  data,
  onDataChanged,
}: {
  data: Task[]
  onDataChanged?: () => void
}) {
  const { openProjectForm } = useModalSystem()
  const [filter, setFilter] = React.useState("")

  const filteredData = React.useMemo(() => {
    const cleanFilter = filter.trim().toLowerCase()
    if (!cleanFilter) return data
    return data.filter((task) => {
      return (
        task.title.toLowerCase().includes(cleanFilter) ||
        task.status.toLowerCase().includes(cleanFilter) ||
        task.priority.toLowerCase().includes(cleanFilter)
      )
    })
  }, [data, filter])

  function convertTaskToProject(task: Task) {
    openProjectForm({
      mode: "create",
      project: {
        name: `Projet - ${task.title}`,
        description: `Projet cree depuis la tache ${task.id}`,
        status: "Planning",
        lead_id: task.lead_id || "",
        due_date: task.due_date || null,
      },
      onSuccess: () => {
        toast.success("Projet cree depuis la tache.")
        onDataChanged?.()
      },
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <Input
          placeholder="Filtrer les taches..."
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          className="sm:max-w-md"
        />
        <p className="text-sm text-muted-foreground">{filteredData.length} tache(s)</p>
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tache</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Priorite</TableHead>
              <TableHead>Echeance</TableHead>
              <TableHead>Assigne a</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.map((task) => (
              <TableRow key={task.id}>
                <TableCell>
                  <div className="font-medium">{task.title}</div>
                  <div className="text-xs text-muted-foreground">#{task.id}</div>
                </TableCell>
                <TableCell>
                  <Badge variant={task.status === "Done" ? "default" : "secondary"}>
                    {task.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={priorityClass(task.priority)}>
                    {task.priority}
                  </Badge>
                </TableCell>
                <TableCell>{formatDateFr(task.due_date || null)}</TableCell>
                <TableCell>{task.assigned_to}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="size-8">
                        <IconDotsVertical className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <DropdownMenuItem onClick={() => convertTaskToProject(task)}>
                        <IconFolderUp className="size-4" />
                        Convertir en projet
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => toast.info("Edition de tache a venir")}> 
                        <IconPencil className="size-4" />
                        Modifier
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => toast.info("Suppression de tache a venir")}> 
                        <IconTrash className="size-4" />
                        Supprimer
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
            {filteredData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
                  Aucune tache ne correspond a votre recherche.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
