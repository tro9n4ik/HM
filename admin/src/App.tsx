import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Setup } from './pages/Setup';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Settings } from './pages/Settings';
import { PluginConfig } from './pages/PluginConfig';
import { PluginLogs } from './pages/PluginLogs';
import { BackupRestore } from './pages/BackupRestore';
import { Logs } from './pages/Logs';
import { Databases } from './pages/Databases';
import { LayoutDashboard, Blocks, Database, ScrollText, Settings as SettingsIcon, LogOut, PanelLeft } from 'lucide-react';

const ProtectedRoute = ({ children, setupRequired }: { children: React.ReactNode, setupRequired: boolean }) => {
  if (setupRequired) {
    return <Navigate to="/setup" />;
  }
  return children;
};

const Sidebar = () => {
  const location = useLocation();
  const path = location.pathname;

  const menuItems = [
    { path: '/', label: 'Обзор', icon: LayoutDashboard },
    { path: '/plugins', label: 'Плагины', icon: Blocks },
    { path: '/databases', label: 'Базы данных', icon: Database },
    { path: '/logs', label: 'Логи', icon: ScrollText },
    { path: '/settings', label: 'Настройки', icon: SettingsIcon },
  ];

  return (
    <nav className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen text-gray-700">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-gray-900 text-white p-1 rounded">
            <span className="font-bold text-xs">HM</span>
          </div>
          <span className="font-semibold text-sm">2.4.12</span>
        </div>
        <PanelLeft className="w-4 h-4 text-gray-400 cursor-pointer hover:text-gray-600" />
      </div>

      <div className="p-4">
        <div className="flex items-center justify-between border border-gray-200 rounded-md px-3 py-1.5 text-sm mb-6 bg-gray-50 cursor-pointer">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
            <span>prod-cluster-01</span>
          </div>
          <span className="text-gray-400 text-xs">↕</span>
        </div>

        <ul className="space-y-1">
          {menuItems.map((item) => {
            const isActive = path === item.path || (item.path !== '/' && path.startsWith(item.path));
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                    isActive ? 'bg-gray-100 text-gray-900 font-medium' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="mt-auto border-t border-gray-200 p-4">
        <div
          className="flex items-center gap-3 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-red-600 rounded-md cursor-pointer transition-colors mb-4"
          onClick={async () => {
            await axios.post('/api/auth/logout');
            window.location.href = '/login';
          }}
        >
          <LogOut className="w-4 h-4" />
          Выйти
        </div>
        <div className="flex items-center justify-between text-xs text-gray-500 px-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
            <span>127.0.0.1</span>
          </div>
          <span className="text-emerald-600">В норме</span>
        </div>
      </div>
    </nav>
  );
};

export function App() {
  const [setupRequired, setSetupRequired] = useState<boolean | null>(null);

  useEffect(() => {
    axios.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401 && window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    axios.get('/api/system/setup-status')
      .then(res => setSetupRequired(res.data.setup_required))
      .catch(() => setSetupRequired(false));
  }, []);

  if (setupRequired === null) return <div>Loading...</div>;

  return (
    <Router>
      <Routes>
        <Route path="/setup" element={setupRequired ? <Setup onSetupComplete={() => setSetupRequired(false)} /> : <Navigate to="/login" />} />
        <Route path="/login" element={setupRequired ? <Navigate to="/setup" /> : <Login />} />

        <Route path="/*" element={
          <ProtectedRoute setupRequired={setupRequired}>
            <div className="flex bg-gray-50 text-gray-900 min-h-screen font-sans">
              <Sidebar />
              <main className="flex-1 overflow-auto bg-gray-50">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  {/* Keep old views functional while redesigning */}
                  <Route path="/plugins" element={<Dashboard />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/backup" element={<BackupRestore />} />
                  <Route path="/logs" element={<Logs />} />
                  <Route path="/databases" element={<Databases />} />
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
