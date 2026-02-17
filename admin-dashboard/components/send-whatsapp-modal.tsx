"use client"

import * as React from "react"
import { IconBrandWhatsapp, IconSend, IconLoader2 } from "@tabler/icons-react"
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

interface SendWhatsAppModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  leadId: string
  leadName: string
  leadPhone: string
  defaultMessage?: string
}

export function SendWhatsAppModal({ 
  open, 
  onOpenChange, 
  leadId, 
  leadName, 
  leadPhone,
  defaultMessage = ""
}: SendWhatsAppModalProps) {
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
      // Log interaction in backend
      await requestApi(`/api/v1/admin/leads/${leadId}/send-whatsapp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      })
      
      // Open WhatsApp Web/App
      const encodedMessage = encodeURIComponent(message)
      const cleanPhone = leadPhone.replace(/\D/g, "")
      window.open(`https://wa.me/${cleanPhone}?text=${encodedMessage}`, "_blank")
      
      toast.success("Interaction WhatsApp enregistrée.")
      onOpenChange(false)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Erreur lors de l'enregistrement.")
    } finally {
      setIsSending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <IconBrandWhatsapp className="size-5 text-green-600" />
            Message WhatsApp pour {leadName}
          </DialogTitle>
          <DialogDescription>
            Rédigez votre message. Après confirmation, WhatsApp s&apos;ouvrira et l&apos;interaction sera logguée.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="whatsapp-message">Message</Label>
            <textarea
              id="whatsapp-message"
              className="min-h-[150px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Votre message WhatsApp..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSending}>
            Annuler
          </Button>
          <Button onClick={handleSend} disabled={isSending} className="bg-green-600 hover:bg-green-700 text-white border-none">
            {isSending ? (
              <IconLoader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <IconSend className="mr-2 size-4" />
            )}
            Envoyer sur WhatsApp
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
