// Local prototype feature flag for admin-only Assembly actions.
// Defaults to admin (true) so Save Current State remains available locally.
// Set VITE_ADMIN_MODE=false for a public-facing preview that hides admin UI.

export function isAdminMode(): boolean {
  const raw = import.meta.env.VITE_ADMIN_MODE;
  if (raw === undefined || raw === "") {
    return true;
  }
  return raw !== "false" && raw !== "0";
}
