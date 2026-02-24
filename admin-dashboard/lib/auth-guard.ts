const PUBLIC_PATHS = new Set(["/", "/login", "/create-account", "/demo"]);
const PUBLIC_PREFIXES = ["/_next/", "/api/", "/images/", "/p/"];
const STATIC_FILE_REGEX = /\.[a-zA-Z0-9]+$/;

// Standard non-sensitive public assets allowed without full authentication
const PUBLIC_FILE_EXTENSIONS = new Set([
  "png", "jpg", "jpeg", "webp", "gif", "css", "ico", "svg", "woff", "woff2", "ttf", "js", "txt", "xml", "json"
]);

export const ACCESS_COOKIE_NAME = "admin_access_token";
export const DEMO_COOKIE_NAME = "prospect_demo";

export function normalizeHostname(hostname: string): string {
  return hostname.trim().toLowerCase();
}

export function isLocalhostHost(hostname: string): boolean {
  const normalized = normalizeHostname(hostname);
  return normalized === "localhost" || normalized === "127.0.0.1";
}

export function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  if (PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return true;
  }
  
  // Restricted extension check for static files
  const lastDotIndex = pathname.lastIndexOf(".");
  if (lastDotIndex !== -1) {
    const extension = pathname.slice(lastDotIndex + 1).toLowerCase();
    if (PUBLIC_FILE_EXTENSIONS.has(extension)) {
      return true;
    }
  }
  
  return false;
}

export function isDemoAccessAllowed(
  hostname: string,
  hasDemoCookie: boolean,
): boolean {
  if (!hasDemoCookie) return false;
  
  // Also allow staging/preview hosts if configured
  const stagingHosts = (process.env.PROSPECT_STAGING_HOSTS || "").split(",");
  return stagingHosts.some(h => normalizeHostname(h) === normalizeHostname(hostname));
}

export function isRouteAuthenticated({
  hostname,
  hasAccessCookie,
  hasDemoCookie,
}: {
  hostname: string;
  hasAccessCookie: boolean;
  hasDemoCookie: boolean;
}): boolean {
  // BYPASS AUTH FOR DEV/TEST - Only with explicit secondary flag or on localhost
  if (
    (process.env.NODE_ENV === "development" || process.env.NODE_ENV === "test") &&
    (process.env.DISABLE_AUTH === "true" || isLocalhostHost(hostname))
  ) {
    return true;
  }

  // Real auth logic: must have access cookie, OR be allowed demo access (which is restricted above)
  return hasAccessCookie || isDemoAccessAllowed(hostname, hasDemoCookie);
}
