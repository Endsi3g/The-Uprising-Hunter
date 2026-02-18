"use client"

import * as React from "react"
import useSWR from "swr"
import { IconCalendar, IconMapPin, IconLink, IconDotsVertical, IconCheck, IconX, IconClock } from "@tabler/icons-react"
import { format, isSameDay, parseISO } from "date-fns"
import { fr } from "date-fns/locale"

import { AppShell } from "@/components/layout/app-shell"
import { SyncStatus } from "@/components/sync-status"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calendar } from "@/components/ui/calendar"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { fetchApi, requestApi } from "@/lib/api"
import { toast } from "sonner"

type Appointment = {
  id: string
  lead_id: string
  title: string
  description?: string
  start_at: string
  end_at: string
  status: string
  location?: string
  meeting_link?: string
  lead_name?: string // We might need to fetch lead names if not in the response
}

const fetcher = <T,>(path: string) => fetchApi<T>(path)

export default function AppointmentsPage() {
  const [selectedDate, setSelectedDate] = React.useState<Date | undefined>(new Date())
  const { data: appointments, error, isLoading, mutate } = useSWR<Appointment[]>(
    "/api/v1/admin/appointments",
    fetcher
  )
  const [updatedAt, setUpdatedAt] = React.useState<Date | null>(null)

  React.useEffect(() => {
    if (!appointments) return
    setUpdatedAt(new Date())
  }, [appointments])

  const filteredAppointments = React.useMemo(() => {
    if (!appointments || !selectedDate) return []
    return appointments.filter(apt => isSameDay(parseISO(apt.start_at), selectedDate))
  }, [appointments, selectedDate])

  const upcomingAppointments = React.useMemo(() => {
    if (!appointments) return []
    return appointments
      .filter(apt => parseISO(apt.start_at) > new Date())
      .sort((a, b) => parseISO(a.start_at).getTime() - parseISO(b.start_at).getTime())
      .slice(0, 5)
  }, [appointments])

  async function updateStatus(id: string, status: string) {
    try {
      await requestApi(`/api/v1/admin/appointments/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status })
      })
      toast.success(`Statut mis à jour : ${status}`)
      await mutate()
    } catch (error) {
      toast.error("Erreur lors de la mise à jour.")
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Rendez-vous</h2>
        <Button onClick={() => toast.info("Veuillez passer par la fiche d'un lead pour programmer un RDV.")}>
          <IconCalendar className="mr-2 h-4 w-4" />
          Nouveau rendez-vous
        </Button>
      </div>
      
      <SyncStatus updatedAt={updatedAt} onRefresh={() => void mutate()} />

      <div className="mt-6 grid gap-6 md:grid-cols-[300px_1fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader className="p-4">
              <CardTitle className="text-base font-semibold">Calendrier</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={setSelectedDate}
                className="w-full"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="p-4">
              <CardTitle className="text-base font-semibold">Prochains RDV</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              {upcomingAppointments.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">Aucun RDV à venir.</p>
              ) : (
                upcomingAppointments.map(apt => (
                  <div key={apt.id} className="text-sm space-y-1">
                    <p className="font-medium truncate">{apt.title}</p>
                    <div className="flex items-center text-xs text-muted-foreground">
                      <IconClock className="mr-1 h-3 w-3" />
                      {format(parseISO(apt.start_at), "d MMMM HH:mm", { locale: fr })}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            {selectedDate ? format(selectedDate, "PPPP", { locale: fr }) : "Sélectionnez une date"}
          </h3>

          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : error ? (
            <ErrorState title="Erreur" description="Impossible de charger les rendez-vous." />
          ) : filteredAppointments.length === 0 ? (
            <EmptyState 
              title="Aucun rendez-vous ce jour" 
              description="Sélectionnez une autre date ou programmez un nouveau rendez-vous."
            />
          ) : (
            filteredAppointments.map(apt => (
              <Card key={apt.id} className="overflow-hidden">
                <div className="flex">
                  <div className="bg-primary w-1" />
                  <div className="flex-1 p-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold">{apt.title}</h4>
                          <Badge variant={apt.status === "scheduled" ? "secondary" : "outline"}>
                            {apt.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {format(parseISO(apt.start_at), "HH:mm", { locale: fr })} - {format(parseISO(apt.end_at), "HH:mm", { locale: fr })}
                        </p>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <IconDotsVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => updateStatus(apt.id, "completed")}>
                            <IconCheck className="mr-2 h-4 w-4" /> Marquer comme terminé
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateStatus(apt.id, "cancelled")} className="text-destructive">
                            <IconX className="mr-2 h-4 w-4" /> Annuler
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateStatus(apt.id, "no-show")}>
                            <IconClock className="mr-2 h-4 w-4" /> Absent (No-show)
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    <div className="mt-4 grid gap-2 sm:grid-cols-2">
                      {apt.location && (
                        <div className="flex items-center text-sm">
                          <IconMapPin className="mr-2 h-4 w-4 text-muted-foreground" />
                          {apt.location}
                        </div>
                      )}
                      {apt.meeting_link && (
                        <div className="flex items-center text-sm">
                          <IconLink className="mr-2 h-4 w-4 text-muted-foreground" />
                          <a href={apt.meeting_link} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline truncate">
                            {apt.meeting_link}
                          </a>
                        </div>
                      )}
                    </div>

                    {apt.description && (
                      <div className="mt-4 p-3 bg-accent/50 rounded-md text-sm italic text-muted-foreground">
                        {apt.description}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </AppShell>
  )
}
