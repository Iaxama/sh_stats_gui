import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Nav from './components/Nav';
import Home from './pages/Home';
import Players from './pages/Players';
import PlayerProfile from './pages/PlayerProfile';
import AddGame from './pages/AddGame';
import History from './pages/History';
import Stats from './pages/Stats';

export default function App() {
  // Sync data with remote repository on app load
  useEffect(() => {
    const syncData = async () => {
      try {
        const response = await fetch('/api/sync/pull');
        if (response.ok) {
          const result = await response.json();
          console.log('Data sync successful:', result);
        } else if (response.status === 503) {
          // Git sync not configured, app continues normally
          console.log('Git sync not configured');
        } else {
          console.warn('Data sync failed:', response.status);
        }
      } catch (error) {
        console.warn('Could not sync data:', error);
        // Continue even if sync fails - app can work offline
      }
    };

    syncData();
  }, []);

  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/players" element={<Players />} />
        <Route path="/players/:playerId" element={<PlayerProfile />} />
        <Route path="/add-game" element={<AddGame />} />
        <Route path="/history" element={<History />} />
        <Route path="/stats" element={<Stats />} />
      </Routes>
    </BrowserRouter>
  );
}
