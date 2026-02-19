"use client"

import * as React from "react"
import { IconCalendar, IconCheck, IconLoader2, IconMapPin, IconLink, IconVideo } from "@tabler/icons-react"
import { toast } from "sonner"
import { format } from "date-fns"
import { fr } from "date-fns/locale"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { requestApi } from "@/lib/api"

interface BookAppointmentModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  leadId: string
  leadName: string
  onSuccess?: () => void
}

export function BookAppointmentModal({ 
  open, 
  onOpenChange, 
  leadId, 
  leadName,
  onSuccess
}: BookAppointmentModalProps) {
  const [title, setTitle] = React.useState(`Rendez-vous avec ${leadName}`)
  const [description, setDescription] = React.useState("")
  const [date, setDate] = React.useState<Date | undefined>(new Date())
  const [time, setTime] = React.useState("10:00")
  const [duration, setDuration] = React.useState("30")
  const [location, setLocation] = React.useState("")
  const [meetingLink, setMeetingLink] = React.useState("")
  const [isBooking, setIsBooking] = React.useState(false)

  function handleGenerateMeetLink() {
    const randomId = Math.random().toString(36).substring(2, 6) + "-" + Math.random().toString(36).substring(2, 6)
    const link = `https://meet.google.com/plh-${randomId}`
    setMeetingLink(link)
    toast.success("Lien Google Meet (placeholder) généré")
  }

  async function handleBook() {
    if (!date) {
      toast.error("Veuillez sélectionner une date.")
      return
    }

    setIsBooking(true)
    try {
      // Combine date and time
      const [hours, minutes] = time.split(":").map(Number)
      const startAt = new Date(date)
      startAt.setHours(hours, minutes, 0, 0)
      
      const endAt = new Date(startAt)
      endAt.setMinutes(startAt.getMinutes() + parseInt(duration, 10))

      await requestApi("/api/v1/admin/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lead_id: leadId,
          title,
          description,
          start_at: startAt.toISOString(),
          end_at: endAt.toISOString(),
          location,
          meeting_link: meetingLink,
          status: "scheduled"
        }),
      })
      
      toast.success("Rendez-vous programmé avec succès !")
      onOpenChange(false)
      if (onSuccess) onSuccess()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Erreur lors de la programmation.")
    } finally {
      setIsBooking(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <IconCalendar className="size-5 text-primary" />
            Programmer un rendez-vous avec {leadName}
          </DialogTitle>
          <DialogDescription>
            Planifiez une réunion et ajoutez les détails de connexion.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="apt-title">Titre du rendez-vous</Label>
            <Input 
              id="apt-title" 
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Démo produit, Appel de découverte..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !date && "text-muted-foreground"
                    )}
                  >
                    <IconCalendar className="mr-2 h-4 w-4" />
                    {date ? format(date, "PPP", { locale: fr }) : <span>Choisir une date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={date}
                    onSelect={setDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
            <div className="space-y-2">
              <Label htmlFor="apt-time">Heure</Label>
              <Input 
                id="apt-time" 
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="apt-duration">Durée (minutes)</Label>
              <Input 
                id="apt-duration" 
                type="number"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="apt-location">Lieu / Bureau</Label>
              <div className="relative">
                <IconMapPin className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                  id="apt-location" 
                  className="pl-9"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Ex: Bureau Paris"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="apt-link">Lien de réunion</Label>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                onClick={handleGenerateMeetLink}
                type="button"
              >
                <IconVideo className="mr-1.5 h-3 w-3" />
                Générer Google Meet
              </Button>
            </div>
            <div className="relative">
              <IconLink className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input 
                id="apt-link" 
                className="pl-9"
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
                placeholder="https://meet.google.com/..."
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="apt-desc">Description / Notes</Label>
            <textarea
              id="apt-desc"
              className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Objectifs de la réunion..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isBooking}>
            Annuler
          </Button>
          <Button onClick={handleBook} disabled={isBooking}>
            {isBooking ? (
              <IconLoader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <IconCheck className="mr-2 size-4" />
            )}
            Confirmer le rendez-vous
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
