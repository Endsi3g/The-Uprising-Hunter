"use client"

import * as React from "react"
import { IconCirclePlusFilled } from "@tabler/icons-react"
import { Button } from "@/components/ui/button"
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetFooter,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { requestApi } from "@/lib/api"

export function AddLeadSheet() {
    const [isOpen, setIsOpen] = React.useState(false)
    const [isLoading, setIsLoading] = React.useState(false)

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setIsLoading(true)

        const formData = new FormData(event.currentTarget)
        const data = {
            first_name: formData.get("firstName"),
            last_name: formData.get("lastName"),
            email: formData.get("email"),
            phone: formData.get("phone"),
            company_name: formData.get("company"),
            status: formData.get("status"),
            segment: formData.get("segment"),
        }

        try {
            await requestApi("/api/v1/admin/leads", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            })

            toast.success("Lead cree avec succes.")
            setIsOpen(false)
            window.dispatchEvent(new Event("prospect:lead-created"))
        } catch (_error) {
            toast.error("Erreur pendant la creation du lead.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
                <Button
                    className="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground active:bg-primary/90 active:text-primary-foreground h-11 w-full rounded-xl px-4 font-bold shadow-lg transition-all duration-200"
                    aria-label="Ouvrir le formulaire de creation de lead"
                >
                    <IconCirclePlusFilled className="!size-5" />
                    <span>Creation rapide de lead</span>
                </Button>
            </SheetTrigger>
            <SheetContent className="sm:max-w-[425px] rounded-l-xl">
                <form onSubmit={onSubmit}>
                    <SheetHeader>
                        <SheetTitle>Ajouter un lead</SheetTitle>
                        <SheetDescription>
                            Creez un nouveau lead manuellement pour alimenter votre pipeline.
                        </SheetDescription>
                    </SheetHeader>
                    <div className="grid gap-6 py-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="firstName">Prenom</Label>
                                <Input id="firstName" name="firstName" placeholder="Jean" required />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="lastName">Nom</Label>
                                <Input id="lastName" name="lastName" placeholder="Dupont" required />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input id="email" name="email" type="email" placeholder="john@company.com" required />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="phone">Telephone</Label>
                            <Input id="phone" name="phone" placeholder="+1 (555) 000-0000" />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="company">Entreprise</Label>
                            <Input id="company" name="company" placeholder="Acme Inc." required />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="status">Statut</Label>
                                <Select name="status" defaultValue="NEW">
                                    <SelectTrigger id="status">
                                        <SelectValue placeholder="Choisir un statut" />
                                    </SelectTrigger>
                                    <SelectContent className="rounded-xl">
                                        <SelectItem value="NEW">Nouveau</SelectItem>
                                        <SelectItem value="SCORED">Score</SelectItem>
                                        <SelectItem value="CONTACTED">Contacte</SelectItem>
                                        <SelectItem value="INTERESTED">Interesse</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="segment">Segment</Label>
                                <Select name="segment" defaultValue="General">
                                    <SelectTrigger id="segment">
                                        <SelectValue placeholder="Choisir un segment" />
                                    </SelectTrigger>
                                    <SelectContent className="rounded-xl">
                                        <SelectItem value="General">General</SelectItem>
                                        <SelectItem value="Enterprise">Enterprise</SelectItem>
                                        <SelectItem value="SMB">SMB</SelectItem>
                                        <SelectItem value="Startup">Startup</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>
                    <SheetFooter>
                        <Button type="submit" className="w-full rounded-xl" disabled={isLoading}>
                            {isLoading ? "Creation..." : "Enregistrer"}
                        </Button>
                    </SheetFooter>
                </form>
            </SheetContent>
        </Sheet>
    )
}
