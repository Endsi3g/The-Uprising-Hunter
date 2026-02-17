"use client"

import * as React from "react"
import { IconDeviceMobile, IconSend, IconLoader2 } from "@tabler/icons-react"
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
import { requestApi } from "@/lib/api"

interface SendSMSModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  leadId: string
  leadName: string
  leadPhone: string
  defaultMessage?: string
}

export function SendSMSModal({ 
  open, 
  onOpenChange, 
  leadId, 
  leadName, 
  leadPhone,
  defaultMessage = ""
}: SendSMSModalProps) {
  const [message, setMessage] = React.useState("")
  const [isSending, setIsSending] = React.useState(false)

  React.useEffect(() => {
    if (open) {
      setMessage(defaultMessage || `Bonjour ${leadName.split(' ')[0]}, `)
    }
  }, [open, leadName, defaultMessage])

  async function handleSend() {
    if (!message.trim()) {
      toast.error("Message requis.")
      return
    }

    setIsSending(true)
    try {
      // In a real app, the backend calls Twilio or similar
      await requestApi(`/api/v1/admin/leads/${leadId}/send-sms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      })
      
      toast.success("SMS envoyé et loggué avec succès !")
      onOpenChange(false)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Erreur lors de l'envoi.")
    } finally {
      setIsSending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <IconDeviceMobile className="size-5 text-blue-600" />
            Envoyer un SMS à {leadName}
          </DialogTitle>
          <DialogDescription>
            Le message sera envoyé via la passerelle SMS et enregistré dans l&apos;historique.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="sms-message">Message (max 160 caractères)</Label>
            <textarea
              id="sms-message"
              className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Votre message SMS..."
              value={message}
              onChange={(e) => setMessage(e.target.value.slice(0, 160))}
            />
            <p className="text-right text-[10px] text-muted-foreground">
              {message.length} / 160
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSending}>
            Annuler
          </Button>
          <Button onClick={handleSend} disabled={isSending} className="bg-blue-600 hover:bg-blue-700 text-white border-none">
            {isSending ? (
              <IconLoader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <IconSend className="mr-2 size-4" />
            )}
            Envoyer par SMS
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
