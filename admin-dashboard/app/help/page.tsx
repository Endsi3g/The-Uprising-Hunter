"use client"

import * as React from "react"
import useSWR from "swr"

import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { requestApi } from "@/lib/api"
import { useI18n } from "@/lib/i18n"
import { requestOnboardingOpen } from "@/lib/onboarding"

type HelpPayload = {
  support_email: string
  faqs: { question: string; answer: string }[]
  links: { label: string; href: string }[]
}

const fetcher = <T,>(path: string) => requestApi<T>(path)

export default function HelpPage() {
  const { messages } = useI18n()
  const { data, error, isLoading } = useSWR<HelpPayload>("/api/v1/admin/help", fetcher)
  const onLaunchOnboarding = React.useCallback(() => {
    requestOnboardingOpen()
  }, [])

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col gap-4 p-3 pt-0 sm:p-4 sm:pt-0 lg:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-3xl font-bold tracking-tight">Centre aide</h2>
            <Button type="button" variant="outline" onClick={onLaunchOnboarding}>
              {messages.onboarding.launchFromHelp}
            </Button>
          </div>
          {isLoading ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-56 w-full lg:col-span-2" />
            </div>
          ) : null}
          {error ? (
            <div className="text-sm text-red-600">Impossible de charger le centre aide.</div>
          ) : null}
          {data ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Support</CardTitle>
                </CardHeader>
                <CardContent>
                  <a href={`mailto:${data.support_email}`} className="underline">
                    {data.support_email}
                  </a>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Liens utiles</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {data.links.map((link) => (
                    <a
                      key={link.href}
                      href={link.href}
                      className="block text-sm underline"
                      target={link.href.startsWith("http") ? "_blank" : undefined}
                      rel={link.href.startsWith("http") ? "noreferrer noopener" : undefined}
                    >
                      {link.label}
                    </a>
                  ))}
                </CardContent>
              </Card>
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>FAQ</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {data.faqs.map((faq) => (
                    <div key={faq.question} className="rounded-lg border p-3">
                      <p className="font-semibold">{faq.question}</p>
                      <p className="text-sm text-muted-foreground">{faq.answer}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}


