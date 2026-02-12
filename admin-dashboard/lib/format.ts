const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "medium",
})

const datetimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "medium",
  timeStyle: "short",
})

const numberFormatter = new Intl.NumberFormat("fr-FR")

const currencyFormatter = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
})

export function formatDateFr(value?: string | null): string {
  if (!value) return "-"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "-"
  return dateFormatter.format(date)
}

export function formatDateTimeFr(value?: string | null): string {
  if (!value) return "-"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "-"
  return datetimeFormatter.format(date)
}

export function formatNumberFr(value?: number | null): string {
  return numberFormatter.format(value ?? 0)
}

export function formatCurrencyFr(value?: number | null): string {
  return currencyFormatter.format(value ?? 0)
}

