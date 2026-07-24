/**
 * One-shot gift-burst banner for new users who get 3 free V1 Ask questions.
 * Backend grants quota (ask_v1_free_questions_used = 0 → 3 left);
 * this only controls the celebration UI (once per account on device).
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

const pendingKey = (userId: string) => `cosmic.welcomeBonus.pending.${userId}`;
const seenKey = (userId: string) => `cosmic.welcomeBonus.seen.${userId}`;

function uid(userId: string | number | null | undefined): string {
  if (userId == null || userId === "") return "";
  return String(userId);
}

/** Call right after signup (is_new_user) so Home can show the gift once. */
export async function markWelcomeBonusPending(
  userId: string | number | null | undefined,
): Promise<void> {
  const id = uid(userId);
  if (!id) return;
  try {
    const seen = await AsyncStorage.getItem(seenKey(id));
    if (seen === "1") return;
    await AsyncStorage.setItem(pendingKey(id), "1");
  } catch {
    /* ignore storage errors */
  }
}

export async function wasWelcomeBonusSeen(
  userId: string | number | null | undefined,
): Promise<boolean> {
  const id = uid(userId);
  if (!id) return true;
  try {
    return (await AsyncStorage.getItem(seenKey(id))) === "1";
  } catch {
    return false;
  }
}

export async function shouldShowWelcomeBonus(
  userId: string | number | null | undefined,
): Promise<boolean> {
  const id = uid(userId);
  if (!id) return false;
  try {
    const [pending, seen] = await Promise.all([
      AsyncStorage.getItem(pendingKey(id)),
      AsyncStorage.getItem(seenKey(id)),
    ]);
    return pending === "1" && seen !== "1";
  } catch {
    return false;
  }
}

/** Mark shown so it never repeats for this account on this device. */
export async function markWelcomeBonusSeen(
  userId: string | number | null | undefined,
): Promise<void> {
  const id = uid(userId);
  if (!id) return;
  try {
    await AsyncStorage.multiSet([
      [seenKey(id), "1"],
      [pendingKey(id), "0"],
    ]);
  } catch {
    /* ignore */
  }
}
