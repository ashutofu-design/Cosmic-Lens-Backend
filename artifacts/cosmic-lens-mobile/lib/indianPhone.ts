/** Normalize Indian mobile for WhatsApp delivery — accepts +91, 91, leading 0, spaces. */
export function normalizeIndianWhatsApp(raw: string): string | null {
  let digits = (raw || "").replace(/\D/g, "");
  if (digits.startsWith("0091") && digits.length >= 14) {
    digits = digits.slice(4);
  } else if (digits.startsWith("91") && digits.length >= 12) {
    digits = digits.slice(2);
  }
  if (digits.startsWith("0") && digits.length === 11) {
    digits = digits.slice(1);
  }
  if (digits.length !== 10) return null;
  return `+91${digits}`;
}

export function indianWhatsAppHint(): string {
  return "10-digit mobile (e.g. 9876543210). +91 optional.";
}

export function humanizeContactError(code: string): string {
  if (code === "invalid_whatsapp") {
    return `Invalid WhatsApp number. ${indianWhatsAppHint()}`;
  }
  if (code === "invalid_email") return "Valid email address daalo.";
  if (code === "contact_required") return "WhatsApp number or email required.";
  return code;
}
