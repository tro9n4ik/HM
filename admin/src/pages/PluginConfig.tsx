import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Save, Plus, ArrowLeft } from 'lucide-react';

export function PluginConfig() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [config, setConfig] = useState<any>({});
  const [schema, setSchema] = useState<any>({});
  const [pluginName, setPluginName] = useState<string>('');
  const [msg, setMsg] = useState('');
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [configRes, schemaRes, pluginRes] = await Promise.all([
          axios.get(`/api/plugins/${id}/config`),
          axios.get(`/api/plugins/${id}/schema`),
          axios.get('/api/plugins')
        ]);

        const pName = pluginRes.data.find((p: any) => p.id === id)?.name || id;
        setPluginName(pName);

        const initialConfig = { ...configRes.data };
        Object.entries(schemaRes.data).forEach(([key, field]: [string, any]) => {
          if (initialConfig[key] === undefined && field.default !== undefined) {
             initialConfig[key] = field.default;
          }
        });
        setConfig(initialConfig);
        setSchema(schemaRes.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchData();
  }, [id]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.put(`/api/plugins/${id}/config`, { config });
      setMsg('Настройки сохранены');
      setIsError(false);
      setTimeout(() => navigate('/'), 1500);
    } catch (err: any) {
      setMsg(`Ошибка сохранения: ${err.response?.data?.detail || err.message}`);
      setIsError(true);
    }
  };

  const handleAdd = () => {
    const key = prompt("Имя ключа (ручное добавление):");
    if (key) setConfig({...config, [key]: ""});
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6 text-sm text-gray-500">
        <div>
          <span>Плагины <span className="text-gray-300 mx-2">/</span> Настройка <span className="text-gray-300 mx-2">/</span> </span>
          <span className="font-semibold text-gray-700">{pluginName}</span>
        </div>
        <Link to="/" className="flex items-center gap-1 hover:text-gray-900 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Назад к списку
        </Link>
      </div>

      <div className="bg-white p-8 border border-gray-200 rounded-lg shadow-sm">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">Настройка плагина</h1>

        {msg && (
          <div className={`mb-6 px-4 py-3 rounded text-sm ${isError ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-emerald-50 text-emerald-600 border border-emerald-200'}`}>
            {msg}
          </div>
        )}

        <form onSubmit={handleSave} className="max-w-3xl">
          {Object.entries(config).map(([key, value]) => {
            const fieldDef = schema[key] || {};
            const isSecret = fieldDef.type === "secret";
            const isBoolean = fieldDef.type === "bool" || fieldDef.type === "boolean";
            const isJson = fieldDef.type === "json";

            return (
              <div className="mb-6" key={key}>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  {fieldDef.title || key}
                  {fieldDef.description && <span className="text-gray-400 font-normal ml-2 text-xs">— {fieldDef.description}</span>}
                </label>

                {isBoolean ? (
                   <label className="flex items-center gap-2 cursor-pointer mt-2">
                     <input
                       type="checkbox"
                       checked={value === true || value === "true"}
                       onChange={e => setConfig({...config, [key]: e.target.checked})}
                       className="w-5 h-5 bg-white border-gray-300 rounded text-emerald-600 focus:ring-emerald-500"
                     />
                     <span className="text-sm text-gray-600">Включено</span>
                   </label>
                ) : isJson ? (
                   <textarea
                     value={typeof value === 'object' ? JSON.stringify(value, null, 2) : value as string}
                     onChange={e => setConfig({...config, [key]: e.target.value})}
                     rows={4}
                     className="w-full p-2.5 rounded-md bg-white border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-sm font-mono"
                   />
                ) : (
                  <input
                    type={isSecret && value !== "***" ? "password" : "text"}
                    value={value as string}
                    onChange={e => setConfig({...config, [key]: e.target.value})}
                    placeholder={isSecret ? "Скрыто" : ""}
                    className="w-full p-2.5 rounded-md bg-white border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-sm"
                  />
                )}
              </div>
            );
          })}

          {Object.keys(schema).length === 0 && Object.keys(config).length === 0 && (
             <p className="text-gray-500 mb-6 text-sm italic">Для этого плагина не найдено настроек.</p>
          )}

          <div className="flex gap-4 border-t border-gray-100 pt-6 mt-8">
            <button
              type="submit"
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-md font-medium transition-colors text-sm"
            >
              <Save className="w-4 h-4" />
              Сохранить
            </button>
            <button
              type="button"
              onClick={handleAdd}
              className="flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-6 py-2.5 rounded-md font-medium transition-colors text-sm"
            >
              <Plus className="w-4 h-4 text-gray-500" />
              Добавить ключ
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
