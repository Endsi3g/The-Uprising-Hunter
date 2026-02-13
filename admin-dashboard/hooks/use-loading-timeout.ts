"use client"

import * as React from "react"

export function useLoadingTimeout(isLoading: boolean, timeoutMs = 12_000): boolean {
  const [timedOut, setTimedOut] = React.useState(false)

  React.useEffect(() => {
    if (!isLoading) {
      setTimedOut(false)
      return
    }

    const timeoutId = window.setTimeout(() => setTimedOut(true), timeoutMs)
    return () => window.clearTimeout(timeoutId)
  }, [isLoading, timeoutMs])

  return timedOut
}
