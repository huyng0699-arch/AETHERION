export type Route = 'portal' | 'login' | 'health' | 'monitor' | 'ai' | 'science' | 'mission' | 'care' | 'settings' | 'more' | 'connection' | 'notifications' | 'help' | 'privacy' | 'appearance' | 'demoIntro' | 'demoData' | 'settingAccount' | 'settingConnection' | 'settingLanguage';
export type Navigation = { route: Route; history: Route[]; pending: Route };
export const initialNavigation: Navigation = { route: 'login', history: [], pending: 'portal' };
export const protectedRoutes: Route[] = ['health', 'monitor', 'ai', 'care', 'mission', 'portal'];
export type NavAction = { type: 'open'; route: Route; unlocked: boolean; tab?: boolean } | { type: 'back' } | { type: 'signedIn' } | { type: 'signedOut'; pending?: Route };
export function navigate(state: Navigation, action: NavAction): Navigation {
  if (action.type === 'signedOut') return { route: 'login', history: [], pending: action.pending || 'portal' };
  if (action.type === 'signedIn') return { route: state.pending === 'login' ? 'portal' : state.pending, history: [], pending: 'portal' };
  if (action.type === 'back') return { ...state, route: state.history.at(-1) || 'login', history: state.history.slice(0, -1) };
  const gate = protectedRoutes.includes(action.route) && !action.unlocked;
  const next = gate ? 'login' : action.route;
  if (next === state.route && !gate) return state;
  return { route: next, history: action.tab ? [] : next === state.route ? state.history : [...state.history, state.route], pending: gate ? action.route : state.pending };
}
