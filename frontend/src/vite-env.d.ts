/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  /** When "false" or "0", hide Assembly admin actions (Save / Export). Default: admin. */
  readonly VITE_ADMIN_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
