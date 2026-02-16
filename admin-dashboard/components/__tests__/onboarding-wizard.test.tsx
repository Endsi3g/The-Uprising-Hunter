import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard"

const steps = [
  {
    id: "dashboard",
    title: "Dashboard",
    description: "Review your KPIs.",
    href: "/dashboard",
    ctaLabel: "Open dashboard",
  },
  {
    id: "leads",
    title: "Leads",
    description: "Manage your lead list.",
    href: "/leads",
    ctaLabel: "Open leads",
  },
]

describe("OnboardingWizard", () => {
  it("renders current step and handles actions", async () => {
    const user = userEvent.setup()
    const onPrevious = vi.fn()
    const onNext = vi.fn()
    const onSkip = vi.fn()
    const onFinish = vi.fn()
    const onNavigate = vi.fn()

    render(
      <OnboardingWizard
        open
        saving={false}
        stepIndex={0}
        steps={steps}
        progressLabel="Step 1 of 2"
        previousLabel="Previous"
        nextLabel="Next"
        skipLabel="Skip"
        finishLabel="Finish"
        onOpenChange={vi.fn()}
        onPrevious={onPrevious}
        onNext={onNext}
        onSkip={onSkip}
        onFinish={onFinish}
        onNavigate={onNavigate}
      />,
    )

    expect(screen.getByText("Dashboard")).toBeInTheDocument()
    expect(screen.getByText("Step 1 of 2")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "Open dashboard" }))
    await user.click(screen.getByRole("button", { name: "Next" }))
    await user.click(screen.getByRole("button", { name: "Skip" }))

    expect(onNavigate).toHaveBeenCalledWith("/dashboard")
    expect(onNext).toHaveBeenCalledTimes(1)
    expect(onSkip).toHaveBeenCalledTimes(1)
    expect(onPrevious).not.toHaveBeenCalled()
    expect(onFinish).not.toHaveBeenCalled()
  })

  it("shows finish action on final step", async () => {
    const user = userEvent.setup()
    const onFinish = vi.fn()

    render(
      <OnboardingWizard
        open
        saving={false}
        stepIndex={1}
        steps={steps}
        progressLabel="Step 2 of 2"
        previousLabel="Previous"
        nextLabel="Next"
        skipLabel="Skip"
        finishLabel="Finish"
        onOpenChange={vi.fn()}
        onPrevious={vi.fn()}
        onNext={vi.fn()}
        onSkip={vi.fn()}
        onFinish={onFinish}
        onNavigate={vi.fn()}
      />,
    )

    expect(screen.getByText("Leads")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Next" })).not.toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "Finish" }))
    expect(onFinish).toHaveBeenCalledTimes(1)
  })
})

