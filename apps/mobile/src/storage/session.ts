import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { AuthSession } from '../types';

const SESSION_KEY = 'aetherion.mobile.session.v1';

// SecureStore operations complete asynchronously. Serialize reads and writes
// so a late logout or old sign-in cannot replace a newer session.
let sessionOperations: Promise<void> = Promise.resolve();
function inSessionOrder<T>(action: () => Promise<T>): Promise<T> {
  const result = sessionOperations.then(action, action);
  sessionOperations = result.then(() => undefined, () => undefined);
  return result;
}

export function readSession(): Promise<AuthSession | null> {
  return inSessionOrder(async () => {
    try {
      const raw = Platform.OS === 'web'
        ? (typeof sessionStorage === 'undefined' ? null : sessionStorage.getItem(SESSION_KEY))
        : await SecureStore.getItemAsync(SESSION_KEY);
      return raw ? JSON.parse(raw) as AuthSession : null;
    } catch {
      return null;
    }
  });
}

export function writeSession(session: AuthSession): Promise<void> {
  return inSessionOrder(async () => {
    const raw = JSON.stringify(session);
    if (Platform.OS === 'web') {
      if (typeof sessionStorage === 'undefined') throw new Error('SESSION_STORAGE_UNAVAILABLE');
      sessionStorage.setItem(SESSION_KEY, raw);
      return;
    }
    await SecureStore.setItemAsync(SESSION_KEY, raw, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  });
}

export function deleteSession(): Promise<void> {
  return inSessionOrder(async () => {
    if (Platform.OS === 'web') {
      if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem(SESSION_KEY);
      return;
    }
    await SecureStore.deleteItemAsync(SESSION_KEY);
  });
}

