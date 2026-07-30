interface TopBarProps {
  drawerOpen: boolean;
  onToggleDrawer: () => void;
}

export function TopBar({ drawerOpen, onToggleDrawer }: TopBarProps) {
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
      <h1 className="font-serif text-2xl font-bold text-terracotta">Nutshell</h1>
    </header>
  );
}
