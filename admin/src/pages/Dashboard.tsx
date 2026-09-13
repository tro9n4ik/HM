import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Search, RotateCcw, MoreHorizontal, Play, Square, Trash2 } from 'lucide-react';
import PluginInstallCard from '../components/PluginInstallCard';

export function Dashboard() {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [install, setInstall] = useState<{fileName: string, state: 'idle' | 'uploading' | 'installing' | 'done' | 'error', error?: string} | null>(null);
  const [systemStats, setSystemStats] = useState<any>({
    cpu: { load: '--', percent: 0 },
    memory: { total: '--', used: '--', percent: 0 },
    storage: { total: '--', used: '--', percent: 0 },
  });
  const [healthChecks, setHealthChecks] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);

  // State to track which plugin's dropdown menu is open
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  // Ref for handling click outside
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        const res = await axios.get('/api/plugins');
        setPlugins(res.data);
      } catch (e) {
        console.error(e);
      }
    };

    const fetchSystemData = async () => {
      try {
        const statsRes = await axios.get('/api/system/stats').catch(() => null);
        if (statsRes?.data) setSystemStats(statsRes.data);

        const healthRes = await axios.get('/api/system/health').catch(() => null);
        if (healthRes?.data) setHealthChecks(healthRes.data);

        const activityRes = await axios.get('/api/system/activity').catch(() => null);
        if (activityRes?.data) setActivities(activityRes.data);
      } catch (e) {
        console.error(e);
      }
    };

    fetchPlugins();
    fetchSystemData();
    const interval = setInterval(() => {
      fetchPlugins();
      fetchSystemData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle click outside to close menu
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuRef]);

  const handleDelete = async (plugin: any) => {
    if (window.confirm(`Удалить плагин ${plugin.name}? Это действие нельзя отменить.`)) {
      try {
        if (plugin.status === 'running' || plugin.status === 'degraded') {
          await axios.post(`/api/plugins/${plugin.id}/stop`);
        }
        await axios.delete(`/api/plugins/${plugin.id}`);
        const res = await axios.get('/api/plugins');
        setPlugins(res.data);
      } catch (e: any) {
        alert("Ошибка удаления: " + (e.response?.data?.detail || e.message));
      }
    }
    setOpenMenuId(null);
  };

  const handleStartStop = async (plugin: any) => {
    try {
      if (plugin.status === 'running' || plugin.status === 'degraded') {
        await axios.post(`/api/plugins/${plugin.id}/stop`);
      } else {
        await axios.post(`/api/plugins/${plugin.id}/start`);
      }
      const res = await axios.get('/api/plugins');
      setPlugins(res.data);
    } catch (e: any) {
       alert("Ошибка: " + (e.response?.data?.detail || e.message));
    }
    setOpenMenuId(null);
  };

  const runningCount = plugins.filter(p => p.status === 'running').length;
  const cpuPercent = systemStats?.cpu?.percent || 0;
  const memPercent = systemStats?.memory?.percent || 0;
  const storagePercent = systemStats?.storage?.percent || 0;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center text-sm text-gray-500 mb-6">
        <div className="w-2 h-2 rounded-full bg-emerald-500 mr-2"></div>
        <span>Local Production <span className="text-gray-300 mx-2">/</span></span>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 border border-gray-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold text-gray-500 uppercase">Процессор</span>
            <span className="text-xs text-gray-400"></span>
          </div>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-3xl font-light text-gray-900">{cpuPercent > 0 ? `${cpuPercent.toFixed(1)}%` : '--'}</span>
            <span className="text-xs text-gray-400">{systemStats?.cpu?.load !== '--' ? `${systemStats.cpu.load} нагрузка` : ''}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5">
            <div className="bg-gray-800 h-1.5 rounded-full" style={{ width: `${cpuPercent}%` }}></div>
          </div>
        </div>

        <div className="bg-white p-5 border border-gray-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold text-gray-500 uppercase">Память</span>
            <span className="text-xs text-gray-400">{systemStats?.memory?.total !== '--' ? `${systemStats.memory.used} / ${systemStats.memory.total}` : '--'}</span>
          </div>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-3xl font-light text-gray-900">{memPercent > 0 ? `${memPercent.toFixed(1)}%` : '--'}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 flex">
            <div className="bg-emerald-500 h-1.5 rounded-l-full" style={{ width: `${memPercent}%` }}></div>
          </div>
        </div>

        <div className="bg-white p-5 border border-gray-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold text-gray-500 uppercase">Хранилище</span>
            <span className="text-xs text-gray-400">{systemStats?.storage?.total !== '--' ? `${systemStats.storage.used} / ${systemStats.storage.total}` : '--'}</span>
          </div>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-3xl font-light text-gray-900">{storagePercent > 0 ? `${storagePercent.toFixed(1)}%` : '--'}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 flex">
            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${storagePercent}%` }}></div>
          </div>
        </div>

        <div className="bg-white p-5 border border-gray-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold text-gray-500 uppercase">Сервисы</span>
            <span className="text-xs text-gray-400">{runningCount} активно</span>
          </div>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-3xl font-light text-gray-900">{runningCount}<span className="text-xl text-gray-400">/{plugins.length}</span></span>
            <span className="text-xs text-emerald-600 font-medium"></span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 flex">
            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${plugins.length > 0 ? (runningCount / plugins.length) * 100 : 0}%` }}></div>
          </div>
        </div>
      </div>

      {/* Main Services List */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm mb-8" ref={menuRef}>
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex gap-6 text-sm">
            <div className="font-semibold text-gray-900 border-b-2 border-gray-900 pb-4 -mb-4">Все ({plugins.length})</div>
            <div className="text-gray-500 hover:text-gray-900 cursor-pointer pb-4 -mb-4">Работают ({runningCount})</div>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2" />
              <input
                type="text"
                placeholder="Фильтр..."
                className="pl-9 pr-4 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-300 w-64"
              />
            </div>
            <label className="cursor-pointer bg-emerald-600 text-white px-4 py-1.5 rounded-md text-sm font-medium hover:bg-emerald-700 transition-colors">
              Установить плагин
              <input type="file" className="hidden" accept=".hm" onChange={async (e) => {
                if (e.target.files && e.target.files[0]) {
                  const file = e.target.files[0];
                  setInstall({ fileName: file.name, state: 'uploading' });

                  const formData = new FormData();
                  formData.append('file', file);

                  try {
                    setInstall({ fileName: file.name, state: 'installing' });
                    await axios.post('/api/plugins/install', formData);
                    setInstall({ fileName: file.name, state: 'done' });

                    const res = await axios.get('/api/plugins');
                    setPlugins(res.data);

                    setTimeout(() => setInstall(null), 3000);
                  } catch (err: any) {
                    setInstall({ fileName: file.name, state: 'error', error: err.response?.data?.detail || 'Не удалось установить' });
                    setTimeout(() => setInstall(null), 5000);
                  }
                  e.target.value = ''; // Reset input
                }
              }} />
            </label>
          </div>
        </div>

        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-400 uppercase bg-white border-b border-gray-100">
            <tr>
              <th className="px-6 py-4 font-semibold">Сервис</th>
              <th className="px-6 py-4 font-semibold">Версия</th>
              <th className="px-6 py-4 font-semibold">Статус</th>
              <th className="px-6 py-4 font-semibold text-right">Действия</th>
            </tr>
          </thead>
          <tbody>
            {plugins.map((p) => (
              <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${p.status === 'running' ? 'bg-emerald-500' : 'bg-yellow-400'}`}></div>
                    <span className="font-medium text-gray-900">{p.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600">v{p.version}</td>
                <td className="px-6 py-4 text-gray-600">{p.status}</td>
                <td className="px-6 py-4 text-right flex items-center justify-end gap-3 relative">
                  <Link to={`/plugins/${p.id}/logs`} className="text-gray-400 hover:text-gray-600">Логи</Link>
                  <Link to={`/plugins/${p.id}/config`} className="text-gray-400 hover:text-gray-600">Настройки</Link>
                  <button onClick={() => axios.post(`/api/plugins/${p.id}/restart`)} className="text-gray-400 hover:text-gray-600">
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <div className="relative">
                    <button
                        onClick={() => setOpenMenuId(openMenuId === p.id ? null : p.id)}
                        className="text-gray-400 hover:text-gray-600 p-1"
                    >
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                    {openMenuId === p.id && (
                        <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-10 py-1">
                           <button
                              onClick={() => handleStartStop(p)}
                              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                           >
                              {p.status === 'running' || p.status === 'degraded' ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                              {p.status === 'running' || p.status === 'degraded' ? 'Остановить' : 'Запустить'}
                           </button>
                           <button
                              onClick={() => handleDelete(p)}
                              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 border-t border-gray-100"
                           >
                              <Trash2 className="w-4 h-4" />
                              Удалить
                           </button>
                        </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {plugins.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  Нет установленных плагинов
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Bottom Layout for Activity and Health */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-white p-6 border border-gray-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xs font-semibold text-gray-500 uppercase">Последняя активность</h3>
            <div className="flex items-center gap-2 text-sm text-emerald-600">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
              подключено
            </div>
          </div>
          <div className="space-y-4">
            {activities.length > 0 ? activities.map((act, i) => (
              <div key={i} className="flex justify-between text-sm">
                <div className="flex gap-4">
                  <span className="text-gray-400 font-mono text-xs w-16">{act.time}</span>
                  <span className="text-gray-700">{act.message}</span>
                </div>
                <span className="text-gray-400 text-xs">{act.source}</span>
              </div>
            )) : (
              <div className="text-sm text-gray-500">Нет недавней активности</div>
            )}
          </div>
        </div>

        <div className="col-span-1 bg-white p-6 border border-gray-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xs font-semibold text-gray-500 uppercase">Проверки здоровья</h3>
            <span className="text-xs border border-gray-200 bg-gray-50 text-gray-700 px-2 py-0.5 rounded">{healthChecks.filter(h => h.status === 'ok').length}/{healthChecks.length}</span>
          </div>
          <div className="space-y-4 text-sm">
            {healthChecks.length > 0 ? healthChecks.map((check, i) => (
              <div key={i} className="flex justify-between pb-3 border-b border-gray-50 last:border-0 last:pb-0">
                <span className="text-gray-700">{check.name}</span>
                <span className={check.status === 'ok' ? 'text-emerald-600' : 'text-red-500'}>{check.message}</span>
              </div>
            )) : (
              <div className="text-sm text-gray-500">Нет данных о проверках</div>
            )}
          </div>
        </div>
      </div>

      {install && <PluginInstallCard fileName={install.fileName} state={install.state} error={install.error} />}
    </div>
  );
}
