import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

function storageKey(userId: number): string {
  return `cl_api_key_${userId}`;
}

/**
 * Keystore/Keychain entry stays on this device: it is never synced to iCloud
 * and never restored onto a different handset from a backup.
 */
const SECURE_OPTIONS: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

export async function loadApiKey(userId: number): Promise<string | null> {
  if (Platform.OS === "web") {
    return AsyncStorage.getItem(storageKey(userId));
  }
  try {
    return await SecureStore.getItemAsync(storageKey(userId), SECURE_OPTIONS);
  } catch {
    return null;
  }
}

export async function saveApiKey(userId: number, apiKey: string): Promise<void> {
  if (!apiKey) return;
  if (Platform.OS === "web") {
    await AsyncStorage.setItem(storageKey(userId), apiKey);
    return;
  }
  await SecureStore.setItemAsync(storageKey(userId), apiKey, SECURE_OPTIONS);
}

export async function clearApiKey(userId: number): Promise<void> {
  if (Platform.OS === "web") {
    await AsyncStorage.removeItem(storageKey(userId));
    return;
  }
  try {
    await SecureStore.deleteItemAsync(storageKey(userId), SECURE_OPTIONS);
  } catch {
    /* already cleared */
  }
}

export function userWithoutApiKey<T extends { api_key?: string | null }>(user: T): Omit<T, "api_key"> {
  const { api_key: _removed, ...rest } = user;
  return rest;
}
