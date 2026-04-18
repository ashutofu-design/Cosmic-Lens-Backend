/**
 * Tiny in-memory cache to hand off the AstroVastu PRO scan result from the
 * scan page to the dedicated result page. Avoids serialising the (large)
 * report through expo-router params.
 */
let _cached: any = null;

export const proResultCache = {
  set(value: any) { _cached = value; },
  get(): any { return _cached; },
  clear() { _cached = null; },
};
