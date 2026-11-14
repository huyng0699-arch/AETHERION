import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { AuthSession } from '../types';

const SESSION_KEY = 'aetherion.mobile.session.v1';

export async function readSession(): Promise<AuthSession | null> {
  try {
    const raw = Platform.OS === 'web'
      ? (typeof sessionStorage === 'undefined' ? null : sessionStorage.getItem(SESSION_KEY))
      : await SecureStore.getItemAsync(SESSION_KEY);
    return raw ? JSON.parse(raw) as AuthSession : null;
  } catch {
    return null;
  }
}

export async function writeSession(session: AuthSession): Promise<void> {
  const raw = JSON.stringify(session);
  if (Platform.OS === 'web') {
    if (typeof sessionStorage === 'undefined') throw new Error('SESSION_STORAGE_UNAVAILABLE');
    sessionStorage.setItem(SESSION_KEY, raw);
    return;
  }
  await SecureStore.setItemAsync(SESSION_KEY, raw, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
}

export async function deleteSession(): Promise<void> {
  if (Platform.OS === 'web') {
    if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem(SESSION_KEY);
    return;
  }
  await SecureStore.deleteItemAsync(SESSION_KEY);
}
