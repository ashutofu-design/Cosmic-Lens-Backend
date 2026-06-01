/**
 * Smart Scan — gallery upload (side tile).
 * Picks a room photo → Photo Engine suggests room type → user confirms room + direction.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { UploadRejectModal } from "@/components/UploadRejectModal";

import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import {
  pickFloorPlanImageNative,
  pickFloorPlanImageOnWeb,
} from "@/lib/floorPlanFilePick";
import { classifyRoomPhoto } from "@/lib/roomPhotoClassify";

export type SmartScanUploadResult = {
  data_url: string;
  base64: string;
  room_type: string;
  direction: string;
  heading_deg?: number;
};

const ROOM_OPTIONS: {
  key: string;
  icon: keyof typeof Feather.glyphMap;
  /** Engine room_type when different from chip key */
  engineKey?: string;
}[] = [
  { key: "bedroom", icon: "moon" },
  { key: "kitchen", icon: "coffee" },
  { key: "bathroom", icon: "droplet" },
  { key: "living", icon: "tv" },
  { key: "pooja", icon: "sun" },
  { key: "office", icon: "briefcase", engineKey: "study" },
  { key: "entrance", icon: "log-in" },
  { key: "study", icon: "book-open" },
  { key: "store", icon: "package" },
  { key: "basement", icon: "layers" },
  { key: "garage", icon: "box" },
  { key: "toilet", icon: "minus-circle", engineKey: "bathroom" },
];

function engineRoomType(chipKey: string): string {
  const opt = ROOM_OPTIONS.find((o) => o.key === chipKey);
  return opt?.engineKey || chipKey;
}

const DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"] as const;

function headingToDirCode(h: number): string {
  const a = ((h % 360) + 360) % 360;
  if (a >= 337.5 || a < 22.5) return "N";
  if (a >= 22.5 && a < 67.5) return "NE";
  if (a >= 67.5 && a < 112.5) return "E";
  if (a >= 112.5 && a < 157.5) return "SE";
  if (a >= 157.5 && a < 202.5) return "S";
  if (a >= 202.5 && a < 247.5) return "SW";
  if (a >= 247.5 && a < 292.5) return "W";
  return "NW";
}

export type CameraCapturePayload = {
  data_url: string;
  base64: string;
  heading_deg?: number;
};

type Props = {
  onSubmit: (result: SmartScanUploadResult) => void;
  loading?: boolean;
  disabled?: boolean;
  userId: number;
  apiKey: string;
  lang?: string;
  roomLabel?: (key: string) => string;
  /** After live camera shutter — open confirm with compass direction. */
  cameraCapture?: CameraCapturePayload | null;
  onCameraCaptureHandled?: () => void;
};

export function SmartScanRoomUpload({
  onSubmit,
  loading,
  disabled,
  userId,
  apiKey,
  lang,
  roomLabel,
  cameraCapture,
  onCameraCaptureHandled,
}: Props) {
  const C = useC();
  const t = useT() as Record<string, string | undefined>;
  const label = roomLabel ?? ((k: string) => k.replace(/_/g, " "));

  const [picking, setPicking] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [open, setOpen] = useState(false);
  const [dataUrl, setDataUrl] = useState("");
  const [base64, setBase64] = useState("");
  const [roomType, setRoomType] = useState("");
  const [direction, setDirection] = useState("");
  const [detectHint, setDetectHint] = useState<string | null>(null);
  const [headingDeg, setHeadingDeg] = useState<number | undefined>(undefined);
  const [roomPhotoOk, setRoomPhotoOk] = useState(false);
  const [rejectBanner, setRejectBanner] = useState<{ message: string; previewUrl: string } | null>(
    null,
  );

  const busy = picking || classifying || !!loading;

  const rejectUpload = useCallback(
    (title: string, message: string, previewUrl?: string, centered = false) => {
      setOpen(false);
      setDataUrl("");
      setBase64("");
      setRoomType("");
      setDirection("");
      setDetectHint(null);
      setHeadingDeg(undefined);
      setRoomPhotoOk(false);
      if (centered && previewUrl) {
        setRejectBanner({ message, previewUrl });
        return;
      }
      Alert.alert(title, message);
    },
    [],
  );

  const openConfirm = useCallback(
    async (
      pickedUrl: string,
      pickedB64: string,
      initialDirection = "",
      compassNote?: string,
      captureHeading?: number,
    ) => {
      setDataUrl(pickedUrl);
      setBase64(pickedB64);
      setRoomType("");
      setDirection(initialDirection);
      setHeadingDeg(
        typeof captureHeading === "number" ? captureHeading : undefined,
      );
      setDetectHint(compassNote ?? null);
      setRoomPhotoOk(false);
      setOpen(true);
      setClassifying(true);
      try {
        const res = await classifyRoomPhoto(pickedUrl, { userId, apiKey, lang });
        if (!res.ok || res.valid_room_photo === false) {
          const isNotRoom =
            res.error === "not_a_room_photo" || res.valid_room_photo === false;
          const notRoomMsg =
            "This does not look like an indoor room photo. Upload a clear picture of one room only (bedroom, bathroom, kitchen, office, etc.).";
          rejectUpload(
            isNotRoom ? "Room photo only" : "Photo not accepted",
            isNotRoom
              ? notRoomMsg
              : res.message ||
                "Please upload one interior room photo (bedroom, bathroom, kitchen, office). Not floor plans.",
            pickedUrl,
            isNotRoom,
          );
          return;
        }
        setRoomPhotoOk(true);
        const detected = (res.detected_room_type || "").toLowerCase();
        if (detected === "office" || detected === "cabin") {
          setRoomType("office");
        } else if (res.suggested_room_type) {
          const chip = ROOM_OPTIONS.find(
            (o) =>
              o.key === res.suggested_room_type ||
              o.engineKey === res.suggested_room_type,
          );
          setRoomType(chip?.key || res.suggested_room_type);
        }
        if (res.hint) {
          setDetectHint(
            compassNote ? `${compassNote} ${res.hint}` : res.hint,
          );
        } else if (res.suggested_room_type) {
          setDetectHint(
            `Suggested: ${label(res.suggested_room_type)} (${
              res.confidence ?? "—"
            }% match) — confirm below.`,
          );
        } else {
          setDetectHint(
            compassNote ||
              "Pick the room type and direction below, then run your report.",
          );
        }
      } catch (e: unknown) {
        setDetectHint(
          e instanceof Error ? e.message : "Auto-detect failed — pick room manually.",
        );
      } finally {
        setClassifying(false);
      }
    },
    [apiKey, label, lang, rejectUpload, userId],
  );

  useEffect(() => {
    if (!cameraCapture) return;
    const b64 =
      cameraCapture.base64 ||
      (cameraCapture.data_url.includes(",")
        ? cameraCapture.data_url.split(",")[1]
        : "");
    const dir =
      typeof cameraCapture.heading_deg === "number"
        ? headingToDirCode(cameraCapture.heading_deg)
        : "";
    const compassNote =
      dir && typeof cameraCapture.heading_deg === "number"
        ? `${t.avp_confirmCompassLocked || "Compass at shutter"}: ${dir} · ${cameraCapture.heading_deg.toFixed(0)}°`
        : undefined;
    void openConfirm(
      cameraCapture.data_url,
      b64,
      dir,
      compassNote,
      cameraCapture.heading_deg,
    );
    onCameraCaptureHandled?.();
  }, [cameraCapture, onCameraCaptureHandled, openConfirm, t.avp_confirmCompassLocked]);

  const onPicked = useCallback(
    (picked: { data_url?: string; base64?: string } | null) => {
      if (!picked) return;
      const b64 =
        picked.base64 ??
        (picked.data_url?.includes(",") ? picked.data_url.split(",")[1] : "") ??
        "";
      if (!b64) {
        Alert.alert("Upload failed", "Could not read this image.");
        return;
      }
      if (b64.length > 13 * 1024 * 1024) {
        Alert.alert("File too large", "Please pick an image under 10 MB.");
        return;
      }
      const url =
        picked.data_url ?? `data:image/jpeg;base64,${b64}`;
      void openConfirm(url, b64);
    },
    [openConfirm],
  );

  const pickImage = useCallback(() => {
    if (disabled || busy) return;
    Haptics.selectionAsync().catch(() => {});
    setPicking(true);

    if (Platform.OS === "web") {
      pickFloorPlanImageOnWeb((picked) => {
        setPicking(false);
        onPicked(picked);
      });
      return;
    }

    void (async () => {
      try {
        const picked = await pickFloorPlanImageNative();
        onPicked(picked);
      } catch (e: unknown) {
        Alert.alert(
          "Couldn't open gallery",
          e instanceof Error ? e.message : String(e),
        );
      } finally {
        setPicking(false);
      }
    })();
  }, [busy, disabled, onPicked]);

  const close = useCallback(() => {
    if (loading || classifying) return;
    setOpen(false);
    setDataUrl("");
    setBase64("");
    setRoomType("");
    setDirection("");
    setDetectHint(null);
    setHeadingDeg(undefined);
    setRoomPhotoOk(false);
  }, [classifying, loading]);

  const submit = useCallback(() => {
    if (!dataUrl || !roomType || !direction || loading || !roomPhotoOk) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onSubmit({
      data_url: dataUrl,
      base64,
      room_type: engineRoomType(roomType),
      direction,
      ...(typeof headingDeg === "number" ? { heading_deg: headingDeg } : {}),
    });
    close();
  }, [base64, close, dataUrl, direction, headingDeg, loading, onSubmit, roomType]);

  const canSubmit =
    !!dataUrl &&
    !!roomType &&
    !!direction &&
    roomPhotoOk &&
    !loading &&
    !classifying;

  return (
    <>
      <Pressable
        onPress={pickImage}
        disabled={disabled || busy}
        style={({ pressed }) => [
          s.sideBtn,
          {
            borderColor: C.accent,
            backgroundColor: C.accentBg,
            opacity: disabled || loading ? 0.5 : pressed ? 0.85 : 1,
          },
        ]}
      >
        {picking || classifying ? (
          <ActivityIndicator color={C.accent} />
        ) : (
          <>
            <Feather name="image" size={26} color={C.accent} />
            <Text style={[s.sideTitle, { color: C.accent }]} numberOfLines={2}>
              Upload{"\n"}Photo
            </Text>
          </>
        )}
      </Pressable>

      <Modal visible={open} animationType="slide" onRequestClose={close} statusBarTranslucent>
        <View style={[s.modalWrap, { backgroundColor: C.bg }]}>
          <View style={[s.modalHeader, { borderColor: C.border }]}>
            <Pressable onPress={close} hitSlop={10} style={{ padding: 6 }}>
              <Feather name="x" size={22} color={C.text} />
            </Pressable>
            <Text style={[s.modalTitle, { color: C.text }]}>
              {t.avp_confirmRoomTitle || "What room is this?"}
            </Text>
            <View style={{ width: 28 }} />
          </View>

          <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
            {dataUrl ? (
              <View>
                <Image source={{ uri: dataUrl }} style={s.preview} resizeMode="cover" />
                {typeof headingDeg === "number" && direction ? (
                  <View style={[s.compassBadge, { backgroundColor: C.accentBg, borderColor: C.accent }]}>
                    <Feather name="compass" size={14} color={C.accent} />
                    <Text style={[s.compassBadgeText, { color: C.text }]}>
                      {headingDeg.toFixed(0)}° · Facing {direction}
                    </Text>
                  </View>
                ) : null}
              </View>
            ) : null}

            {classifying ? (
              <View style={s.detectRow}>
                <ActivityIndicator color={C.accent} />
                <Text style={[s.detectText, { color: C.textMid }]}>
                  Checking room photo…
                </Text>
              </View>
            ) : detectHint ? (
              <Text style={[s.detectText, { color: C.accent, marginTop: 10 }]}>
                {detectHint}
              </Text>
            ) : null}

            <Text style={[s.roomOnlyNote, { color: C.textMid }]}>
              Interior room photo only — bedroom, bathroom, kitchen, office, etc. (not floor plan).
            </Text>

            <Text style={[s.sectionLabel, { color: C.textMid, marginTop: 16 }]}>
              ROOM
            </Text>
            <View style={s.chipGrid}>
              {ROOM_OPTIONS.map((opt) => {
                const sel = opt.key === roomType;
                return (
                  <Pressable
                    key={opt.key}
                    onPress={() => {
                      Haptics.selectionAsync().catch(() => {});
                      setRoomType(opt.key);
                    }}
                    style={[
                      s.roomChip,
                      {
                        borderColor: sel ? C.accent : C.border,
                        backgroundColor: sel ? C.accentBg : C.bgCard,
                      },
                    ]}
                  >
                    <Feather
                      name={opt.icon}
                      size={14}
                      color={sel ? C.accent : C.textMid}
                    />
                    <Text
                      style={{
                        color: sel ? C.accent : C.text,
                        fontSize: 12,
                        fontWeight: "600",
                      }}
                    >
                      {label(opt.key)}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={[s.sectionLabel, { color: C.textMid, marginTop: 16 }]}>
              {(t.avp_confirmPickDirection || "Direction (compass)").toUpperCase()}
            </Text>
            <View style={s.dirRow}>
              {DIRECTIONS.map((d) => {
                const sel = d === direction;
                return (
                  <Pressable
                    key={d}
                    onPress={() => {
                      Haptics.selectionAsync().catch(() => {});
                      setDirection(d);
                    }}
                    style={[
                      s.dirChip,
                      {
                        borderColor: sel ? C.accent : C.border,
                        backgroundColor: sel ? C.accentBg : C.bgCard,
                      },
                    ]}
                  >
                    <Text
                      style={{
                        color: sel ? C.accent : C.text,
                        fontWeight: "800",
                        fontSize: 13,
                      }}
                    >
                      {d}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Pressable
              onPress={submit}
              disabled={!canSubmit}
              style={({ pressed }) => [
                s.submitBtn,
                {
                  backgroundColor: C.accent,
                  opacity: !canSubmit ? 0.45 : pressed ? 0.85 : 1,
                  marginTop: 24,
                },
              ]}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={s.submitText}>
                  {t.avp_runRoomScan || "Get my Vastu report"}
                </Text>
              )}
            </Pressable>
          </ScrollView>
        </View>
      </Modal>

      <UploadRejectModal
        visible={!!rejectBanner}
        onClose={() => setRejectBanner(null)}
        title={t.avp_notRoomPhotoTitle || "This doesn't look like a room photo"}
        message={
          rejectBanner?.message ||
          (t.avp_notRoomPhotoBody ||
            "This does not look like an indoor room photo. Upload a clear picture of one room only (bedroom, bathroom, kitchen, office, etc.).")
        }
        primaryLabel={t.avp_uploadRoomPhotoBtn || "Upload a room photo"}
        previewUrl={rejectBanner?.previewUrl}
        icon="home"
        onPrimary={() => {
          setRejectBanner(null);
          pickImage();
        }}
      />
    </>
  );
}

const s = StyleSheet.create({
  sideBtn: {
    width: "100%",
    minHeight: 108,
    borderRadius: 16,
    borderWidth: 2,
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 10,
    paddingVertical: 14,
    gap: 8,
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 2,
  },
  sideTitle: {
    fontSize: 13,
    fontWeight: "800",
    textAlign: "center",
    lineHeight: 17,
    width: "100%",
  },
  modalWrap: { flex: 1 },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    paddingTop: 52,
    paddingBottom: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalTitle: { fontSize: 16, fontWeight: "800" },
  preview: { width: "100%", height: 200, borderRadius: 12 },
  compassBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  compassBadgeText: { fontSize: 14, fontWeight: "800", flex: 1 },
  detectRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 12,
  },
  detectText: { fontSize: 12, lineHeight: 17, flex: 1 },
  roomOnlyNote: {
    fontSize: 11,
    lineHeight: 16,
    marginTop: 10,
    textAlign: "center",
    fontStyle: "italic",
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.6,
    marginBottom: 8,
  },
  chipGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  roomChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 9,
    paddingHorizontal: 11,
    borderRadius: 9,
    borderWidth: 1,
  },
  dirRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  dirChip: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 9,
    borderWidth: 1,
    minWidth: 52,
    alignItems: "center",
  },
  submitBtn: {
    height: 50,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  submitText: { color: "#fff", fontSize: 16, fontWeight: "800" },
});
