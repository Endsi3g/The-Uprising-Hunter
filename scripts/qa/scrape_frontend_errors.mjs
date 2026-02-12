#!/usr/bin/env node

import fs from "node:fs"
import path from "node:path"

const args = process.argv.slice(2)

function argValue(flag, fallback = "") {
  const index = args.indexOf(flag)
  if (index === -1) return fallback
  return args[index + 1] ?? fallback
}

const outputPath = argValue("--output", path.join("artifacts", "qa", "scrape_latest.json"))
const frontendBaseUrl = argValue("--frontend-url", "http://localhost:3000")
const backendBaseUrl = argValue("--backend-url", "http://localhost:8000")

const pages = [
  "/dashboard",
  "/leads",
  "/tasks",
  "/projects",
  "/settings",
  "/help",
  "/analytics",
]

const suspiciousPatterns = [
  /Unhandled Runtime Error/i,
  /Hydration failed/i,
  /TypeError:/i,
  /ReferenceError:/i,
  /Cannot read properties/i,
  /ChunkLoadError/i,
  /API request failed/i,
  /Erreur de chargement/i,
]

async function scrapePage(route) {
  const url = `${frontendBaseUrl}${route}`
  const started = Date.now()
  try {
    const response = await fetch(url, { cache: "no-store" })
    const body = await response.text()
    const issues = []
    if (response.status >= 500) {
      issues.push({
        severity: "error",
        message: `HTTP ${response.status} for ${route}`,
      })
    }
    for (const pattern of suspiciousPatterns) {
      if (pattern.test(body)) {
        issues.push({
          severity: "warning",
          message: `Pattern '${pattern.source}' detected in ${route}`,
        })
      }
    }
    return {
      route,
      url,
      status: response.status,
      duration_ms: Date.now() - started,
      issues,
    }
  } catch (error) {
    return {
      route,
      url,
      status: 0,
      duration_ms: Date.now() - started,
      issues: [
        {
          severity: "error",
          message: error instanceof Error ? error.message : String(error),
        },
      ],
    }
  }
}

async function checkApi(route) {
  const url = `${backendBaseUrl}${route}`
  const started = Date.now()
  try {
    const response = await fetch(url, { cache: "no-store" })
    const payloadText = await response.text()
    const issues = []
    if (response.status >= 500) {
      issues.push({
        severity: "error",
        message: `API ${route} returned ${response.status}`,
      })
    } else if (response.status >= 400) {
      issues.push({
        severity: "warning",
        message: `API ${route} returned ${response.status}`,
      })
    }
    if (/traceback|exception|internal server error/i.test(payloadText)) {
      issues.push({
        severity: "warning",
        message: `Suspicious error signature found in API payload for ${route}`,
      })
    }
    return {
      route,
      url,
      status: response.status,
      duration_ms: Date.now() - started,
      issues,
    }
  } catch (error) {
    return {
      route,
      url,
      status: 0,
      duration_ms: Date.now() - started,
      issues: [
        {
          severity: "error",
          message: error instanceof Error ? error.message : String(error),
        },
      ],
    }
  }
}

async function main() {
  const pageResults = await Promise.all(pages.map((route) => scrapePage(route)))
  const apiResults = await Promise.all([
    checkApi("/healthz"),
    checkApi("/api/v1/admin/stats"),
  ])

  const issues = [
    ...pageResults.flatMap((entry) => entry.issues.map((issue) => ({ scope: entry.route, ...issue }))),
    ...apiResults.flatMap((entry) => entry.issues.map((issue) => ({ scope: entry.route, ...issue }))),
  ]

  const payload = {
    generated_at: new Date().toISOString(),
    frontend_base_url: frontendBaseUrl,
    backend_base_url: backendBaseUrl,
    pages: pageResults,
    apis: apiResults,
    issue_count: issues.length,
    error_count: issues.filter((issue) => issue.severity === "error").length,
    warning_count: issues.filter((issue) => issue.severity === "warning").length,
    issues,
  }

  fs.mkdirSync(path.dirname(outputPath), { recursive: true })
  fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2), "utf-8")
  process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`)

  if (payload.error_count > 0) {
    process.exitCode = 2
  }
}

main().catch((error) => {
  const payload = {
    generated_at: new Date().toISOString(),
    issue_count: 1,
    error_count: 1,
    warning_count: 0,
    issues: [{ severity: "error", message: error instanceof Error ? error.message : String(error) }],
  }
  fs.mkdirSync(path.dirname(outputPath), { recursive: true })
  fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2), "utf-8")
  process.stderr.write(`${payload.issues[0].message}\n`)
  process.exitCode = 2
})
