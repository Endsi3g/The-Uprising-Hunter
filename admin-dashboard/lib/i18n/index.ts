import { fr } from "./fr"

export const messages = fr

export function t(path: string): string {
  const keys = path.split(".")
  let current: unknown = messages
  for (const key of keys) {
    if (typeof current !== "object" || current === null || !(key in current)) {
      return path
    }
    current = (current as Record<string, unknown>)[key]
  }
  return typeof current === "string" ? current : path
}

