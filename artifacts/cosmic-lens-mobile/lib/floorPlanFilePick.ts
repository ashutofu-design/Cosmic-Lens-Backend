/**
 * Floor-plan file picking helpers.
 *
 * On web, the hidden <input> must be opened synchronously inside the button
 * press handler (no await before .click()). Otherwise browsers block the dialog
 * or throw. Native uses expo-image-picker / expo-document-picker as usual.
 */
import * as DocumentPicker from "expo-document-picker";
import * as ImagePicker from "expo-image-picker";
import { Alert, Platform } from "react-native";

export type PickedFloorPlan = {
  type: "image" | "pdf";
  base64?: string;
  data_url?: string;
  filename?: string;
  size_bytes?: number;
};

const MAX_BYTES = 10 * 1024 * 1024;

function guardSize(n?: number): boolean {
  if (typeof n === "number" && n > MAX_BYTES) {
    Alert.alert(
      "File too large",
      `Floor plan must be under ${MAX_BYTES / (1024 * 1024)} MB.`,
    );
    return false;
  }
  return true;
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = String(reader.result || "");
      const comma = dataUrl.indexOf(",");
      resolve(comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl);
    };
    reader.onerror = () =>
      reject(reader.error ?? new Error("Failed to read the selected file."));
    reader.readAsDataURL(file);
  });
}

function stripDataUrlPrefix(dataUrl: string): string {
  const comma = dataUrl.indexOf(",");
  return comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl;
}

/**
 * Opens the image file dialog synchronously (web only).
 * `onDone` is called when picking finishes or is cancelled.
 */
export function pickFloorPlanImageOnWeb(
  onDone: (file: PickedFloorPlan | null) => void,
): void {
  if (typeof document === "undefined" || !document.body) {
    Alert.alert(
      "Upload unavailable",
      "File upload is not supported in this browser view.",
    );
    onDone(null);
    return;
  }

  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.style.display = "none";
  document.body.appendChild(input);

  const cleanup = () => {
    try {
      if (input.parentNode) input.parentNode.removeChild(input);
    } catch {
      /* already removed */
    }
  };

  input.addEventListener("change", () => {
    void (async () => {
      try {
        const file = input.files?.[0];
        if (!file) {
          onDone(null);
          return;
        }
        if (!guardSize(file.size)) {
          onDone(null);
          return;
        }
        const b64 = await readFileAsBase64(file);
        const mime = file.type || "image/jpeg";
        onDone({
          type: "image",
          data_url: `data:${mime};base64,${b64}`,
          filename: file.name || "floor_plan.jpg",
          size_bytes: file.size,
        });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        Alert.alert("Upload failed", msg);
        onDone(null);
      } finally {
        cleanup();
      }
    })();
  });

  input.click();
}

/**
 * Opens image/PDF dialog synchronously (web only).
 */
export function pickFloorPlanDocOnWeb(
  onDone: (file: PickedFloorPlan | null) => void,
): void {
  if (typeof document === "undefined" || !document.body) {
    Alert.alert(
      "Upload unavailable",
      "File upload is not supported in this browser view.",
    );
    onDone(null);
    return;
  }

  const input = document.createElement("input");
  input.type = "file";
  input.accept = "application/pdf,image/*";
  input.style.display = "none";
  document.body.appendChild(input);

  const cleanup = () => {
    try {
      if (input.parentNode) input.parentNode.removeChild(input);
    } catch {
      /* already removed */
    }
  };

  input.addEventListener("change", () => {
    void (async () => {
      try {
        const file = input.files?.[0];
        if (!file) {
          onDone(null);
          return;
        }
        if (!guardSize(file.size)) {
          onDone(null);
          return;
        }
        const b64 = await readFileAsBase64(file);
        const mime = file.type || "image/jpeg";
        const isPdf =
          mime.includes("pdf") || file.name.toLowerCase().endsWith(".pdf");
        onDone({
          type: isPdf ? "pdf" : "image",
          base64: b64,
          data_url: isPdf ? undefined : `data:${mime};base64,${b64}`,
          filename:
            file.name || (isPdf ? "floor_plan.pdf" : "floor_plan.jpg"),
          size_bytes: file.size,
        });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        Alert.alert("Upload failed", msg);
        onDone(null);
      } finally {
        cleanup();
      }
    })();
  });

  input.click();
}

export async function pickFloorPlanImageNative(): Promise<PickedFloorPlan | null> {
  const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (perm.status !== "granted") {
    Alert.alert(
      "Permission needed",
      "Please allow photo library access to upload your floor plan.",
    );
    return null;
  }
  const r = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ["images"],
    quality: 0.85,
    base64: true,
    exif: false,
  });
  if (r.canceled || !r.assets?.[0]?.base64) return null;
  const a = r.assets[0];
  if (!guardSize(a.fileSize)) return null;
  const mime = a.mimeType || "image/jpeg";
  return {
    type: "image",
    base64: a.base64,
    data_url: `data:${mime};base64,${a.base64}`,
    filename: a.fileName || "floor_plan.jpg",
    size_bytes: a.fileSize,
  };
}

/** PDF-only picker (web) — must run synchronously inside a press handler. */
export function pickPdfOnlyOnWeb(
  onDone: (file: PickedFloorPlan | null) => void,
): void {
  if (typeof document === "undefined" || !document.body) {
    Alert.alert(
      "Upload unavailable",
      "File upload is not supported in this browser view.",
    );
    onDone(null);
    return;
  }

  const input = document.createElement("input");
  input.type = "file";
  input.accept = "application/pdf";
  input.style.display = "none";
  document.body.appendChild(input);

  const cleanup = () => {
    try {
      if (input.parentNode) input.parentNode.removeChild(input);
    } catch {
      /* already removed */
    }
  };

  input.addEventListener("change", () => {
    void (async () => {
      try {
        const file = input.files?.[0];
        if (!file) {
          onDone(null);
          return;
        }
        if (!guardSize(file.size)) {
          onDone(null);
          return;
        }
        const b64 = await readFileAsBase64(file);
        onDone({
          type: "pdf",
          base64: b64,
          data_url: `data:application/pdf;base64,${b64}`,
          filename: file.name || "floor-plan.pdf",
          size_bytes: file.size,
        });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        Alert.alert("Upload failed", msg);
        onDone(null);
      } finally {
        cleanup();
      }
    })();
  });

  input.click();
}

export async function pickPdfOnlyNative(): Promise<PickedFloorPlan | null> {
  const r = await DocumentPicker.getDocumentAsync({
    type: "application/pdf",
    copyToCacheDirectory: true,
    multiple: false,
    base64: Platform.OS === "web",
  });
  if (r.canceled || !r.assets?.[0]) return null;
  const f = r.assets[0];
  if (!guardSize(f.size)) return null;

  if (Platform.OS === "web" && f.base64) {
    const raw =
      typeof f.base64 === "string" && f.base64.startsWith("data:")
        ? stripDataUrlPrefix(f.base64)
        : f.base64;
    return {
      type: "pdf",
      base64: raw,
      data_url: `data:application/pdf;base64,${raw}`,
      filename: f.name || "floor-plan.pdf",
      size_bytes: f.size,
    };
  }

  const FileSystem = await import("expo-file-system/legacy");
  const b64 = await FileSystem.readAsStringAsync(f.uri, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return {
    type: "pdf",
    base64: b64,
    data_url: `data:application/pdf;base64,${b64}`,
    filename: f.name || "floor-plan.pdf",
    size_bytes: f.size,
  };
}

export async function pickFloorPlanDocNative(): Promise<PickedFloorPlan | null> {
  const r = await DocumentPicker.getDocumentAsync({
    type: ["application/pdf", "image/*"],
    copyToCacheDirectory: true,
    multiple: false,
    base64: Platform.OS === "web",
  });
  if (r.canceled || !r.assets?.[0]) return null;
  const f = r.assets[0];
  if (!guardSize(f.size)) return null;

  const isPdf =
    (f.mimeType || "").includes("pdf") ||
    (f.name || "").toLowerCase().endsWith(".pdf");

  if (Platform.OS === "web" && f.base64) {
    const raw =
      typeof f.base64 === "string" && f.base64.startsWith("data:")
        ? stripDataUrlPrefix(f.base64)
        : f.base64;
    return {
      type: isPdf ? "pdf" : "image",
      base64: raw,
      data_url: isPdf
        ? undefined
        : `data:${f.mimeType || "image/jpeg"};base64,${raw}`,
      filename: f.name || (isPdf ? "floor_plan.pdf" : "floor_plan.jpg"),
      size_bytes: f.size,
    };
  }

  const FileSystem = await import("expo-file-system/legacy");
  const b64 = await FileSystem.readAsStringAsync(f.uri, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return {
    type: isPdf ? "pdf" : "image",
    base64: b64,
    data_url: isPdf ? undefined : `data:${f.mimeType || "image/jpeg"};base64,${b64}`,
    filename: f.name || (isPdf ? "floor_plan.pdf" : "floor_plan.jpg"),
    size_bytes: f.size,
  };
}
