export type Theme = 'light' | 'dark';

export const THEME_STORAGE_KEY = 'nutshell-theme';

export function resolveInitialTheme(stored: string | null, prefersDark: boolean): Theme {
  if (stored === 'dark' || stored === 'light') return stored;
  return prefersDark ? 'dark' : 'light';
}
