/** Structured OTP flow tracing — never logs OTP codes or full verification IDs. */
// Dev builds only — EXPO_PUBLIC_OTP_TRACE must not re-enable auth tracing in a
// shipped binary, where the logs are readable via adb logcat.
const OTP_TRACE_ENABLED = __DEV__;

export function redactId(id: string | null | undefined): string {
  if (!id) return "(none)";
  if (id.length <= 10) return `${id.slice(0, 3)}…`;
  return `${id.slice(0, 8)}…${id.slice(-4)}`;
}

export function redactPhone(phoneE164: string): string {
  const digits = String(phoneE164 || "").replace(/\D/g, "");
  if (digits.length < 4) return "****";
  return `***${digits.slice(-4)}`;
}

export function otpTrace(event: string, fields: Record<string, unknown> = {}): void {
  if (!OTP_TRACE_ENABLED) return;
  console.log(`[otp-trace] ${event}`, { timestamp: Date.now(), ...fields });
}
