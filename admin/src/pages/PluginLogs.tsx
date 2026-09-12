import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Terminal } from 'lucide-react';

export function PluginLogs() {
  const { id } = useParams();
  const [logs, setLogs] = useState<string>('');
  const [pluginName, setPluginName] = useState<string>('');
  const preRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const fetchPluginInfo = async () => {
        try {
            const res = await axios.get('/api/plugins');
            const pName = res.data.find((p: any) => p.id === id)?.name || id;
            setPluginName(pName);
        } catch (e) {
            console.error(e);
        }
    };
    fetchPluginInfo();

    const fetchLogs = async () => {
      try {
        const res = await axios.get(`/api/plugins/${id}/logs`);
        setLogs(res.data.logs);
      } catch (e) {
        console.error(e);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => {
    if (preRef.current) {
        preRef.current.scrollTop = preRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="p-8 max-w-6xl mx-auto h-screen flex flex-col">
      <div className="flex justify-between items-center mb-6 text-sm text-gray-500 flex-shrink-0">
        <div>
          <span>Плагины <span className="text-gray-300 mx-2">/</span> Логи <span className="text-gray-300 mx-2">/</span> </span>
          <span className="font-semibold text-gray-700">{pluginName}</span>
        </div>
        <Link to="/" className="flex items-center gap-1 hover:text-gray-900 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Назад к списку
        </Link>
      </div>

      <div className="bg-white p-6 border border-gray-200 rounded-lg shadow-sm flex flex-col flex-1 min-h-0">
        <h1 className="text-2xl font-bold mb-4 text-gray-800 flex items-center gap-2">
            <Terminal className="w-6 h-6 text-gray-400" />
            Логи плагина
        </h1>

        <pre
            ref={preRef}
            className="flex-1 bg-gray-900 p-4 rounded-md text-emerald-400 overflow-auto whitespace-pre-wrap text-xs font-mono border border-gray-800"
        >
          {logs || "Ожидание логов..."}
        </pre>
      </div>
    </div>
  );
}
