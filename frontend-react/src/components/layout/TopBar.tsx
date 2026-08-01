import type { Theme } from '../../lib/theme';
import wordmarkLight from '../../assets/wordmark-light.svg';
import wordmarkDark from '../../assets/wordmark-dark.svg';

interface TopBarProps {
  drawerOpen: boolean;
  onToggleDrawer: () => void;
  theme: Theme;
  onToggleTheme: () => void;
}

export function TopBar({ drawerOpen, onToggleDrawer, theme, onToggleTheme }: TopBarProps) {
  return (
    <header className="flex flex-shrink-0 items-center gap-3 border-b border-warm-gray/30 bg-ivory px-6 py-4 dark:bg-espresso/60">
      <button
        type="button"
        onClick={onToggleDrawer}
        className="rounded p-1.5 text-espresso hover:bg-warm-gray/30 dark:text-cream dark:hover:bg-warm-gray/20"
        aria-label="Toggle navigation drawer"
        aria-expanded={drawerOpen}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <img src={wordmarkLight} alt="Nutshell" className="h-9 w-auto dark:hidden" />
      <img src={wordmarkDark} alt="Nutshell" className="hidden h-9 w-auto dark:block" />
      <button
        type="button"
        onClick={onToggleTheme}
        className="ml-auto rounded p-1.5 text-espresso hover:bg-warm-gray/30 dark:text-cream dark:hover:bg-warm-gray/20"
        aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {theme === 'dark' ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1.5m0 15V21m9-9h-1.5m-15 0H3m15.364-6.364-1.06 1.06M6.696 17.304l-1.06 1.06m12.728 0-1.06-1.06M6.696 6.696l-1.06-1.06M16.5 12a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0Z" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
          </svg>
        )}
      </button>
    </header>
  );
}
