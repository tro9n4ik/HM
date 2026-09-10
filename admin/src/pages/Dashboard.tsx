import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

export function Dashboard() {
  const [plugins, setPlugins] = useState<any[]>([]);

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        const res = await axios.get('/api/plugins');
        setPlugins(res.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchPlugins();
    const interval = setInterval(fetchPlugins, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const formData = new FormData();
      formData.append('file', file);
      await axios.post('/api/plugins/install', formData);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Plugins</h1>
      <div className="mb-8 p-6 border-2 border-dashed border-gray-600 rounded text-center">
        <label className="cursor-pointer text-blue-500 hover:underline">
          Upload .hm Package
          <input type="file" className="hidden" accept=".hm" onChange={handleUpload} />
        </label>
      </div>

      <div className="grid gap-4">
        {plugins.map(p => (
          <div key={p.id} className="bg-gray-800 p-4 rounded flex flex-col gap-4">
            <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-bold text-xl">{p.name} <span className="text-sm text-gray-400">v{p.version}</span></h3>
                  <p>Status: <span className={p.status === 'running' ? 'text-green-500' : 'text-yellow-500'}>{p.status}</span></p>
                  {p.last_error && <p className="text-red-400 text-sm mt-1">{p.last_error}</p>}
                </div>
                <div className="flex gap-2">
                  <button className="bg-blue-600 px-4 py-2 rounded text-sm hover:bg-blue-700" onClick={async () => {
                    await axios.post(`/api/plugins/${p.id}/start`);
                  }}>Start</button>
                  <button className="bg-gray-600 px-4 py-2 rounded text-sm hover:bg-gray-700" onClick={async () => {
                    await axios.post(`/api/plugins/${p.id}/stop`);
                  }}>Stop</button>
                </div>
            </div>
            <div className="flex gap-2 border-t border-gray-700 pt-2">
              <Link to={`/plugins/${p.id}/config`} className="bg-gray-600 px-4 py-2 rounded text-sm hover:bg-gray-700">Config</Link>
              <Link to={`/plugins/${p.id}/logs`} className="bg-gray-600 px-4 py-2 rounded text-sm hover:bg-gray-700">Logs</Link>
              <button className="bg-red-600 px-4 py-2 rounded text-sm hover:bg-red-700" onClick={async () => {
                await axios.post(`/api/plugins/${p.id}/restart`);
              }}>Restart</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
