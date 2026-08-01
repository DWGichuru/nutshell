import { useState } from 'react';
import { resolveInitialTheme, THEME_STORAGE_KEY, type Theme } from '../lib/theme';

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
}

export function useDarkMode() {
  const [theme, setTheme] = useState<Theme>(() => {
    const initial = resolveInitialTheme(
      localStorage.getItem(THEME_STORAGE_KEY),
      window.matchMedia('(prefers-color-scheme: dark)').matches,
    );
    applyTheme(initial);
    return initial;
  });

  function toggleTheme() {
    setTheme((current) => {
      const next: Theme = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem(THEME_STORAGE_KEY, next);
      return next;
    });
  }

  return { theme, toggleTheme };
}
