/**
 * Shared French labels for lead status codes.
 * Import `leadStatusLabel` wherever a status is displayed to the user.
 */
export const LEAD_STATUS_LABELS: Record<string, string> = {
    NEW: "Nouveau",
    ENRICHED: "Enrichi",
    SCORED: "Qualifié",
    CONTACTED: "Contacté",
    INTERESTED: "Engagé",
    CONVERTED: "Converti",
    LOST: "Perdu",
    DISQUALIFIED: "Disqualifié",
};

/** Return the French display label for the given lead status code. Falls back to the raw code. */
export function leadStatusLabel(status: string): string {
    return LEAD_STATUS_LABELS[status] || status;
}
