import { describe, expect, it } from "vitest"

import {
  activateLocalDemoMode,
  disableDemoMode,
  isDemoModeActive,
} from "@/lib/demo-mode"

describe("demo mode helpers", () => {
  it("activates demo mode on localhost", () => {
    window.history.replaceState(null, "", "http://localhost:3000/")
    expect(activateLocalDemoMode()).toBe(true)
    expect(window.localStorage.getItem("prospect:forceMock")).toBe("true")
    expect(document.cookie).toContain("prospect_demo=1")
    expect(isDemoModeActive()).toBe(true)
    disableDemoMode()
    expect(isDemoModeActive()).toBe(false)
  })
})
