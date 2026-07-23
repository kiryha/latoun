import { afterEach, describe, expect, it, vi } from "vitest";

describe("isAdminMode", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("defaults to admin mode when unset", async () => {
    vi.stubEnv("VITE_ADMIN_MODE", "");
    const { isAdminMode } = await import("./adminMode");
    expect(isAdminMode()).toBe(true);
  });

  it("hides admin actions in public mode", async () => {
    vi.stubEnv("VITE_ADMIN_MODE", "false");
    const { isAdminMode } = await import("./adminMode");
    expect(isAdminMode()).toBe(false);
  });

  it("keeps admin actions visible in admin mode", async () => {
    vi.stubEnv("VITE_ADMIN_MODE", "true");
    const { isAdminMode } = await import("./adminMode");
    expect(isAdminMode()).toBe(true);
  });
});
