"use client"

import * as React from "react"
import { IconPhone, IconCheck, IconLoader2 } from "@tabler/icons-react"
import { toast } from "sonner"

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
import { requestApi } from "@/lib/api"

interface LogCallModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  leadId: string
  leadName: string
}

export function LogCallModal({ 
  open, 
  onOpenChange, 
  leadId, 
  leadName 
}: LogCallModalProps) {
  const [notes, setNotes] = React.useState("")
  const [duration, setDuration] = React.useState("60") // seconds
  const [isLogging, setIsLogging] = React.useState(false)

  async function handleLog() {
    setIsLogging(true)
    try {
      await requestApi(`/api/v1/admin/leads/${leadId}/log-call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes, duration: parseInt(duration, 10) }),
      })
      
      toast.success("Appel tracé avec succès !")
      onOpenChange(false)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Erreur lors du traçage.")
    } finally {
      setIsLogging(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <IconPhone className="size-5 text-blue-600" />
            Tracer l&apos;appel avec {leadName}
          </DialogTitle>
          <DialogDescription>
            Enregistrez les détails de votre conversation téléphonique.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="call-duration">Durée estimée (secondes)</Label>
            <Input 
              id="call-duration" 
              type="number" 
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="call-notes">Notes de l&apos;appel</Label>
            <textarea
              id="call-notes"
              className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Quelles sont les prochaines étapes ?"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLogging}>
            Annuler
          </Button>
          <Button onClick={handleLog} disabled={isLogging} className="bg-blue-600 hover:bg-blue-700 text-white border-none">
            {isLogging ? (
              <IconLoader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <IconCheck className="mr-2 size-4" />
            )}
            Valider et Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
