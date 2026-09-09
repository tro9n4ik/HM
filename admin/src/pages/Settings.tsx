import React, { useEffect, useState } from 'react';
import axios from 'axios';

export function Settings() {
  const [settings, setSettings] = useState<any>({});

  useEffect(() => {
    const fetchSettings = async () => {
      const token = localStorage.getItem('token');
      try {
        const res = await axios.get('/api/system/settings', { headers: { Authorization: `Bearer ${token}` } });
        setSettings(res.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    await axios.put('/api/system/settings', { settings }, { headers: { Authorization: `Bearer ${token}` } });
    alert('Saved');
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">System Settings</h1>
      <form onSubmit={handleSave} className="bg-gray-800 p-6 rounded max-w-2xl">
        <div className="mb-4">
          <label className="block mb-2 text-gray-300">Plugin Port Range</label>
          <input
            type="text"
            value={settings['plugin_port_range'] || '8100-8200'}
            onChange={e => setSettings({...settings, plugin_port_range: e.target.value})}
            className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
          />
        </div>
        <div className="mb-6">
          <label className="block mb-2 text-gray-300">PIP Index URL (Mirror)</label>
          <input
            type="text"
            value={settings['pip_index_url'] || ''}
            onChange={e => setSettings({...settings, pip_index_url: e.target.value})}
            className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
            placeholder="https://pypi.org/simple"
          />
        </div>
        <button type="submit" className="bg-blue-600 px-6 py-2 rounded text-white font-bold hover:bg-blue-700">Save</button>
      </form>
    </div>
  );
}
