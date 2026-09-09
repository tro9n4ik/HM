import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

export function PluginLogs() {
  const { id } = useParams();
  const [logs, setLogs] = useState<string>('');

  useEffect(() => {
    const fetchLogs = async () => {
      const token = localStorage.getItem('token');
      try {
        const res = await axios.get(`/api/plugins/${id}/logs`, { headers: { Authorization: `Bearer ${token}` } });
        setLogs(res.data.logs);
      } catch (e) {
        console.error(e);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [id]);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Plugin Logs</h1>
      <pre className="bg-gray-900 p-4 rounded text-green-400 overflow-x-auto whitespace-pre-wrap text-sm border border-gray-700 min-h-[400px]">
        {logs || "No logs available."}
      </pre>
    </div>
  );
}
