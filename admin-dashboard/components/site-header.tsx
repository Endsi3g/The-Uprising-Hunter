"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { IconHelp, IconSearch } from "@tabler/icons-react"

import { useModalSystem } from "@/components/modal-system-provider"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"

const TITLES: Record<string, string> = {
  "/dashboard": "Tableau de bord",
  "/leads": "Leads",
  "/tasks": "Taches",
  "/analytics": "Analytique",
  "/projects": "Projets",
  "/campaigns": "Campagnes",
  "/research": "Recherche",
  "/systems": "Systemes",
  "/settings": "Parametres",
  "/settings/team": "Equipe & roles",
  "/help": "Aide",
  "/library": "Bibliotheque",
  "/reports": "Rapports",
  "/assistant": "Assistant",
  "/account": "Compte",
  "/billing": "Facturation",
  "/notifications": "Notifications",
}

export function SiteHeader() {
  const pathname = usePathname()
  const { openHelp, openSearch } = useModalSystem()
  const title = React.useMemo(() => {
    if (pathname in TITLES) return TITLES[pathname]
    if (pathname.startsWith("/leads/")) return "Fiche lead"
    if (pathname.startsWith("/projects/")) return "Fiche projet"
    if (pathname.startsWith("/tasks/")) return "Fiche tache"
    return "Prospect"
  }, [pathname])

  return (
    <header className="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-3 sm:px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1 size-9 sm:size-7" />
        <Separator
          orientation="vertical"
          className="mx-1 hidden data-[orientation=vertical]:h-4 sm:mx-2 sm:block"
        />
        <h1 className="min-w-0 truncate text-sm font-medium sm:text-base">{title}</h1>
        <div className="ml-auto flex items-center gap-1 sm:gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={openSearch}
            className="h-9 w-9 px-0 sm:h-8 sm:w-auto sm:px-3"
            aria-label="Recherche"
          >
            <IconSearch className="size-4" />
            <span className="sr-only sm:not-sr-only">Recherche</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={openHelp}
            className="h-9 w-9 px-0 sm:h-8 sm:w-auto sm:px-3"
            aria-label="Aide"
          >
            <IconHelp className="size-4" />
            <span className="sr-only sm:not-sr-only">Aide</span>
          </Button>
          <Button variant="ghost" asChild size="sm" className="hidden md:flex">
            <Link href="/settings">Parametres</Link>
          </Button>
        </div>
      </div>
    </header>
  )
}

