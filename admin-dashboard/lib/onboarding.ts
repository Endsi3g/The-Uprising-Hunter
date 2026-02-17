export type OnboardingStatus = "pending" | "skipped" | "completed"

export const ONBOARDING_STATUS_KEY = "onboarding_v1_status"
export const ONBOARDING_SEEN_AT_KEY = "onboarding_v1_seen_at"
export const ONBOARDING_COMPLETED_AT_KEY = "onboarding_v1_completed_at"
export const ONBOARDING_DISMISSED_AT_KEY = "onboarding_v1_dismissed_at"
export const ONBOARDING_OPEN_EVENT = "prospect:onboarding:open"

type Preferences = Record<string, unknown>

function clonePreferences(preferences?: Preferences | null): Preferences {
  return { ...(preferences || {}) }
}

export function getOnboardingStatus(preferences?: Preferences | null): OnboardingStatus {
  const raw = preferences?.[ONBOARDING_STATUS_KEY]
  if (raw === "skipped" || raw === "completed" || raw === "pending") {
    return raw
  }
  return "pending"
}

export function markOnboardingSkipped(preferences?: Preferences | null): Preferences {
  const next = clonePreferences(preferences)
  const now = new Date().toISOString()
  next[ONBOARDING_STATUS_KEY] = "skipped"
  next[ONBOARDING_DISMISSED_AT_KEY] = now
  if (!next[ONBOARDING_SEEN_AT_KEY]) {
    next[ONBOARDING_SEEN_AT_KEY] = now
  }
  return next
}

export function markOnboardingCompleted(preferences?: Preferences | null): Preferences {
  const next = clonePreferences(preferences)
  const now = new Date().toISOString()
  next[ONBOARDING_STATUS_KEY] = "completed"
  next[ONBOARDING_COMPLETED_AT_KEY] = now
  if (!next[ONBOARDING_SEEN_AT_KEY]) {
    next[ONBOARDING_SEEN_AT_KEY] = now
  }
  return next
}

export function requestOnboardingOpen(): void {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent(ONBOARDING_OPEN_EVENT))
}
