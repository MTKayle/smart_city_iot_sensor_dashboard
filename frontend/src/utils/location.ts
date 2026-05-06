import type { Location } from '../types';

/**
 * Resolve a locationId to a friendly Vietnamese label using the
 * full Locations hierarchy (City > District > Ward).
 *
 * - Ward: "Phường Bến Nghé, Quận 1"
 * - District: "Quận 1"
 * - City / unknown / null: returns the raw input or "—"
 */
export function formatLocationName(
  locationId: string | null | undefined,
  locations: Location[],
): string {
  if (!locationId) return '—';
  const node = locations.find((l) => l.locationId === locationId);
  if (!node) return locationId;

  if (node.type === 'Ward' && node.parentId) {
    const parent = locations.find((l) => l.locationId === node.parentId);
    return parent ? `${node.name}, ${parent.name}` : node.name;
  }
  return node.name;
}

/**
 * Short-form: just the leaf name (e.g. "Phường Bến Nghé"), no parent suffix.
 * Use in tight columns where parent context is implicit.
 */
export function shortLocationName(
  locationId: string | null | undefined,
  locations: Location[],
): string {
  if (!locationId) return '—';
  const node = locations.find((l) => l.locationId === locationId);
  return node ? node.name : locationId;
}
