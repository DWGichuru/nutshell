import type { ReactNode } from 'react';

export interface TabDefinition {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: TabDefinition[];
  activeId: string;
  onChange: (id: string) => void;
  children: ReactNode;
}

export function Tabs({ tabs, activeId, onChange, children }: TabsProps) {
  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex gap-1 border-b border-warm-gray/30 bg-ivory px-8 pt-5 dark:bg-espresso/60">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`rounded-t-md px-4 py-2 text-sm font-semibold ${
              tab.id === activeId
                ? 'bg-cream text-terracotta dark:bg-near-black'
                : 'text-warm-gray hover:text-espresso dark:hover:text-cream'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-8">{children}</div>
    </div>
  );
}
