"use client"

import * as React from "react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { formatCurrencyFr } from "@/lib/format"

export type ForecastPoint = {
  month: string
  expected_revenue: number
  weighted_revenue: number
  count: number
}

export interface RevenueForecastChartProps {
  data?: ForecastPoint[]
}

const chartConfig = {
  expected: {
    label: "CA Potentiel",
    color: "var(--muted)",
  },
  weighted: {
    label: "CA Pondéré",
    color: "var(--primary)",
  },
} satisfies ChartConfig

export default function RevenueForecastChart({ data = [] }: RevenueForecastChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Prévisions de revenus</CardTitle>
          <CardDescription>CA estimé basé sur les opportunités ouvertes</CardDescription>
        </CardHeader>
        <CardContent className="flex h-[300px] items-center justify-center text-sm text-muted-foreground border-t">
          Aucune opportunité avec date de clôture prévue.
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prévisions de revenus</CardTitle>
        <CardDescription>CA mensuel (Pondéré vs Potentiel)</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value / 1000}k€`}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  formatter={(value, name) => [
                    formatCurrencyFr(Number(value)),
                    name === "weighted" ? "CA Pondéré" : "CA Potentiel"
                  ]}
                />
              }
            />
            <Bar dataKey="expected_revenue" name="expected" fill="var(--color-expected)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="weighted_revenue" name="weighted" fill="var(--color-weighted)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
