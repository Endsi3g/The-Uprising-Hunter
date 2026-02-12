import { IconListCheck, IconUserPlus, IconUsers } from "@tabler/icons-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface Stats {
  sourced_total: number;
  qualified_total: number;
  contacted_total: number;
  closed_total: number;
  qualified_rate: number;
  close_rate: number;
}

export function SectionCards({ stats }: { stats?: Stats }) {
  // Default values if no stats provided
  const safeStats = stats || {
    sourced_total: 0,
    qualified_total: 0,
    contacted_total: 0,
    closed_total: 0,
    qualified_rate: 0,
    close_rate: 0,
  };

  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Total des leads</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {safeStats.sourced_total}
          </CardTitle>
          <CardAction>
            <IconUsers />
          </CardAction>
        </CardHeader>
          <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Base active
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Leads qualifies</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {safeStats.qualified_total}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <IconUserPlus />
              {safeStats.qualified_rate}%
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Taux de qualification
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Leads contactes</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {safeStats.contacted_total}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <IconListCheck />
              Campagnes
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Touches envoyees
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Opportunites gagnees</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {safeStats.closed_total}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              {safeStats.close_rate}%
            </Badge>
          </CardAction>
        </CardHeader>
      </Card>
    </div>
  )
}
