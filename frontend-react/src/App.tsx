import { useState } from 'react';
import { TopBar } from './components/layout/TopBar';
import { Drawer } from './components/layout/Drawer';
import { NewSummaryPage } from './pages/NewSummaryPage/NewSummaryPage';
import { LibraryPage } from './pages/LibraryPage/LibraryPage';
import { useDarkMode } from './hooks/useDarkMode';

export type Page = 'new-summary' | 'library';

function App() {
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [activePage, setActivePage] = useState<Page>('new-summary');
  const { theme, toggleTheme } = useDarkMode();

  return (
    <div className="min-h-screen bg-cream text-espresso dark:bg-near-black dark:text-cream font-sans">
      <div className="flex h-screen flex-col overflow-hidden">
        <TopBar
          drawerOpen={drawerOpen}
          onToggleDrawer={() => setDrawerOpen((open) => !open)}
          theme={theme}
          onToggleTheme={toggleTheme}
        />
        <div className="flex flex-1 overflow-hidden">
          <Drawer open={drawerOpen} activePage={activePage} onSelectPage={setActivePage} />
          <div className="flex-1 overflow-hidden">
            {activePage === 'new-summary' ? <NewSummaryPage /> : <LibraryPage />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
