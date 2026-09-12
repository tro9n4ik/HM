import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Save } from 'lucide-react';

export function Settings() {
  const [settings, setSettings] = useState<any>({});
  const [msg, setMsg] = useState('');

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await axios.get('/api/system/settings');
        setSettings(res.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.put('/api/system/settings', { settings });
      setMsg('Настройки сохранены');
      setTimeout(() => setMsg(''), 3000);
    } catch {
      setMsg('Ошибка сохранения');
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center text-sm text-gray-500 mb-6">
        <span>Система <span className="text-gray-300 mx-2">/</span> Настройки</span>
      </div>

      <div className="bg-white p-8 border border-gray-200 rounded-lg shadow-sm">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">Системные настройки</h1>

        {msg && (
          <div className="mb-6 px-4 py-3 rounded text-sm bg-emerald-50 text-emerald-600 border border-emerald-200">
            {msg}
          </div>
        )}

        <form onSubmit={handleSave} className="max-w-2xl">
          <div className="mb-6">
            <label className="block mb-2 text-sm font-medium text-gray-700">Диапазон портов для плагинов</label>
            <input
              type="text"
              value={settings['plugin_port_range'] || '8100-8200'}
              onChange={e => setSettings({...settings, plugin_port_range: e.target.value})}
              className="w-full p-2.5 rounded-md bg-white border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">Система будет автоматически назначать свободные порты плагинам из этого диапазона.</p>
          </div>
          <div className="mb-8">
            <label className="block mb-2 text-sm font-medium text-gray-700">PIP Index URL (Зеркало)</label>
            <input
              type="text"
              value={settings['pip_index_url'] || ''}
              onChange={e => setSettings({...settings, pip_index_url: e.target.value})}
              className="w-full p-2.5 rounded-md bg-white border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-sm"
              placeholder="https://pypi.org/simple"
            />
            <p className="mt-1 text-xs text-gray-500">Оставьте пустым для использования стандартного репозитория PyPI.</p>
          </div>

          <div className="border-t border-gray-100 pt-6">
            <button
              type="submit"
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-md font-medium transition-colors text-sm"
            >
              <Save className="w-4 h-4" />
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
