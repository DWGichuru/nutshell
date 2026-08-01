import type { Page } from '../../App';

const ACTIVE_NAV_CLASSES = 'bg-terracotta text-cream hover:bg-terracotta-dark';
const INACTIVE_NAV_CLASSES =
  'bg-ivory text-espresso hover:bg-warm-gray/30 dark:bg-espresso/60 dark:text-cream';

interface DrawerProps {
  open: boolean;
  activePage: Page;
  onSelectPage: (page: Page) => void;
}

export function Drawer({ open, activePage, onSelectPage }: DrawerProps) {
  if (!open) {
    return null;
  }

  return (
    <aside className="flex w-[232px] flex-shrink-0 flex-col gap-7 border-r border-warm-gray/30 bg-ivory p-6 dark:bg-espresso/60">
      <nav className="flex flex-col gap-1.5">
        <button
          type="button"
          onClick={() => onSelectPage('new-summary')}
          className={`block w-full rounded px-3 py-2.5 text-left text-sm font-medium ${
            activePage === 'new-summary' ? ACTIVE_NAV_CLASSES : INACTIVE_NAV_CLASSES
          }`}
        >
          New Summary
        </button>
        <button
          type="button"
          onClick={() => onSelectPage('library')}
          className={`block w-full rounded px-3 py-2.5 text-left text-sm font-medium ${
            activePage === 'library' ? ACTIVE_NAV_CLASSES : INACTIVE_NAV_CLASSES
          }`}
        >
          Library
        </button>
      </nav>
    </aside>
  );
}
