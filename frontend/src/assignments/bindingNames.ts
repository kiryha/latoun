// Binding-name normalization shared by the Assignments tab validation UI.
// Mirrors backend material_assignment_service.normalize_binding_name.

const BINDING_NAME_PATTERN = /^[a-z][a-z0-9_]*$/;

export function normalizeBindingName(rawBindingName: string): string {
  return rawBindingName.trim().toLowerCase().replace(/\s+/g, "_");
}

export function validateBindingName(rawBindingName: string): string | null {
  const normalized = normalizeBindingName(rawBindingName);
  if (!normalized) {
    return "Binding name must not be empty.";
  }
  if (!BINDING_NAME_PATTERN.test(normalized)) {
    return (
      `Invalid binding name “${rawBindingName}”. Use lowercase letters, ` +
      "digits and underscores, starting with a letter (e.g. primary_metal)."
    );
  }
  return null;
}
