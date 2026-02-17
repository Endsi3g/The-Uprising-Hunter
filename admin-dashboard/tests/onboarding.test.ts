import { describe, expect, it, vi } from "vitest"

import {
  getOnboardingStatus,
  markOnboardingCompleted,
  markOnboardingSkipped,
  ONBOARDING_COMPLETED_AT_KEY,
  ONBOARDING_DISMISSED_AT_KEY,
  ONBOARDING_OPEN_EVENT,
  ONBOARDING_SEEN_AT_KEY,
  ONBOARDING_STATUS_KEY,
  requestOnboardingOpen,
} from "@/lib/onboarding"

describe("onboarding helpers", () => {
  it("returns pending by default", () => {
    expect(getOnboardingStatus()).toBe("pending")
    expect(getOnboardingStatus({})).toBe("pending")
    expect(getOnboardingStatus({ [ONBOARDING_STATUS_KEY]: "unknown" })).toBe("pending")
  })

  it("marks onboarding as skipped and keeps existing preferences", () => {
    const current = { theme: "dark", [ONBOARDING_STATUS_KEY]: "pending" }
    const next = markOnboardingSkipped(current)

    expect(next.theme).toBe("dark")
    expect(next[ONBOARDING_STATUS_KEY]).toBe("skipped")
    expect(typeof next[ONBOARDING_DISMISSED_AT_KEY]).toBe("string")
    expect(typeof next[ONBOARDING_SEEN_AT_KEY]).toBe("string")
  })

  it("marks onboarding as completed and keeps existing preferences", () => {
    const current = { theme: "light", [ONBOARDING_STATUS_KEY]: "pending" }
    const next = markOnboardingCompleted(current)

    expect(next.theme).toBe("light")
    expect(next[ONBOARDING_STATUS_KEY]).toBe("completed")
    expect(typeof next[ONBOARDING_COMPLETED_AT_KEY]).toBe("string")
    expect(typeof next[ONBOARDING_SEEN_AT_KEY]).toBe("string")
  })

  it("dispatches onboarding open event", () => {
    const handler = vi.fn()
    window.addEventListener(ONBOARDING_OPEN_EVENT, handler)
    requestOnboardingOpen()
    expect(handler).toHaveBeenCalledTimes(1)
    window.removeEventListener(ONBOARDING_OPEN_EVENT, handler)
  })
})

