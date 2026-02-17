"use client"

import { DEMO_COOKIE_NAME } from "@/lib/auth-guard"

const FORCE_MOCK_STORAGE_KEY = "prospect:forceMock"
const DEMO_COOKIE_MAX_AGE_SECONDS = 86400

function isLocalhostHost(hostname: string): boolean {
  const normalized = hostname.trim().toLowerCase()
  return normalized === "localhost" || normalized === "127.0.0.1"
}

export function activateLocalDemoMode(): boolean {
  if (typeof window === "undefined") return false
  if (!isLocalhostHost(window.location.hostname)) return false

  try {
    window.localStorage.setItem(FORCE_MOCK_STORAGE_KEY, "true")
  } catch {
    // Ignore localStorage failures.
  }

  document.cookie = `${DEMO_COOKIE_NAME}=1; Max-Age=${DEMO_COOKIE_MAX_AGE_SECONDS}; Path=/; SameSite=Lax`
  return true
}

export function isDemoModeActive(): boolean {
  if (typeof window === "undefined") return false

  const hasDemoCookie = document.cookie
    .split(";")
    .map((part) => part.trim())
    .some((part) => part.startsWith(`${DEMO_COOKIE_NAME}=1`))

  let hasForceMock = false
  try {
    hasForceMock = window.localStorage.getItem(FORCE_MOCK_STORAGE_KEY) === "true"
  } catch {
    hasForceMock = false
  }

  return hasDemoCookie || hasForceMock
}

export function disableDemoMode(): void {
  if (typeof window === "undefined") return
  try {
    window.localStorage.removeItem(FORCE_MOCK_STORAGE_KEY)
  } catch {
    // Ignore localStorage failures.
  }
  document.cookie = `${DEMO_COOKIE_NAME}=; Max-Age=0; Path=/; SameSite=Lax`
}
