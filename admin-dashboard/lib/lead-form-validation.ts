export function isValidLeadEmail(email: string): boolean {
  const trimmed = email.trim();
  if (!trimmed) return true;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);
}

export function isValidLeadPhone(phone: string): boolean {
  if (!phone.trim()) return true;
  return /^[+()\d\s-]{6,20}$/.test(phone.trim());
}
