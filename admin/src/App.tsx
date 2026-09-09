import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Setup } from './pages/Setup';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Settings } from './pages/Settings';
import { PluginConfig } from './pages/PluginConfig';
import { PluginLogs } from './pages/PluginLogs';
import { BackupRestore } from './pages/BackupRestore';

const ProtectedRoute = ({ children, setupRequired }: { children: React.ReactNode, setupRequired: boolean }) => {
  if (setupRequired) {
    return <Navigate to="/setup" />;
  }
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" />;
  }
  return children;
};

export function App() {
  const [setupRequired, setSetupRequired] = useState<boolean | null>(null);

  useEffect(() => {
    axios.get('/api/system/setup-status')
      .then(res => setSetupRequired(res.data.setup_required))
      .catch(() => setSetupRequired(false));
  }, []);

  if (setupRequired === null) return <div>Loading...</div>;

  return (
    <Router>
      <Routes>
        <Route path="/setup" element={setupRequired ? <Setup /> : <Navigate to="/login" />} />
        <Route path="/login" element={setupRequired ? <Navigate to="/setup" /> : <Login />} />

        <Route path="/*" element={
          <ProtectedRoute setupRequired={setupRequired}>
            <div className="flex bg-gray-900 text-white min-h-screen">
              <nav className="w-64 bg-gray-800 p-4">
                <h1 className="text-xl font-bold mb-8">Home.Media</h1>
                <ul>
                  <li className="mb-4"><Link to="/" className="hover:text-blue-400">Plugins</Link></li>
                  <li className="mb-4"><Link to="/settings" className="hover:text-blue-400">Settings</Link></li>
                  <li className="mb-4"><Link to="/backup" className="hover:text-blue-400">Backup & Restore</Link></li>
                  <li className="mb-4 cursor-pointer hover:text-red-400" onClick={() => {
                    localStorage.removeItem('token');
                    window.location.href = '/login';
                  }}>Logout</li>
                </ul>
              </nav>
              <main className="flex-1 overflow-auto">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/backup" element={<BackupRestore />} />
                  <Route path="/plugins/:id/config" element={<PluginConfig />} />
                  <Route path="/plugins/:id/logs" element={<PluginLogs />} />
                </Routes>
              </main>
            </div>
          </ProtectedRoute>
        } />
      </Routes>
    </Router>
  );
}
export default App;
