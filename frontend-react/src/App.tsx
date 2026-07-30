import { useState } from 'react';
import { TopBar } from './components/layout/TopBar';
import { Drawer } from './components/layout/Drawer';
import { ResizablePane } from './components/shared/ResizablePane';
import { NewSummaryPage } from './pages/NewSummaryPage/NewSummaryPage';

export type Page = 'new-summary' | 'library';

const RESIZABLE_PANE_BOUNDS = { minWidth: 280, minRemainder: 320 };

function App() {
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [activePage, setActivePage] = useState<Page>('new-summary');

  return (
    <div className="min-h-screen bg-cream text-espresso dark:bg-near-black dark:text-cream font-sans">
      <div className="flex h-screen flex-col overflow-hidden">
        <TopBar drawerOpen={drawerOpen} onToggleDrawer={() => setDrawerOpen((open) => !open)} />
        <div className="flex flex-1 overflow-hidden">
          <Drawer open={drawerOpen} activePage={activePage} onSelectPage={setActivePage} />
          <div className="flex-1 overflow-hidden">
            {activePage === 'new-summary' ? (
              <NewSummaryPage />
            ) : (
              <main className="flex h-full">
                <ResizablePane
                  {...RESIZABLE_PANE_BOUNDS}
                  paneContent={<p>Library interaction pane placeholder.</p>}
                  restContent={
                    <div className="flex h-full items-center justify-center p-10 text-center text-warm-gray">
                      <p>Select a video to see its transcript and summary here.</p>
                    </div>
                  }
                />
              </main>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
