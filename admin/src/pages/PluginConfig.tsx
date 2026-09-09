import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

export function PluginConfig() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [config, setConfig] = useState<any>({});
  const [schema, setSchema] = useState<any>({});

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      try {
        const [configRes, schemaRes] = await Promise.all([
          axios.get(`/api/plugins/${id}/config`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`/api/plugins/${id}/schema`, { headers: { Authorization: `Bearer ${token}` } })
        ]);

        const initialConfig = { ...configRes.data };
        // Populate default values from schema if missing in config
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
    const token = localStorage.getItem('token');
    await axios.put(`/api/plugins/${id}/config`, { config }, { headers: { Authorization: `Bearer ${token}` } });
    alert('Config Saved');
    navigate('/');
  };

  const handleAdd = () => {
    const key = prompt("Config Key (Manual Override):");
    if (key) setConfig({...config, [key]: ""});
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Configure Plugin</h1>
      <form onSubmit={handleSave} className="bg-gray-800 p-6 rounded max-w-2xl">
        {Object.entries(config).map(([key, value]) => {
          const fieldDef = schema[key] || {};
          const isSecret = fieldDef.type === "secret";
          return (
            <div className="mb-4" key={key}>
              <label className="block mb-2 text-gray-300">
                {fieldDef.title || key} {fieldDef.description && <span className="text-gray-500 text-sm ml-2">- {fieldDef.description}</span>}
              </label>
              <input
                type={isSecret && value !== "***" ? "password" : "text"}
                value={value as string}
                onChange={e => setConfig({...config, [key]: e.target.value})}
                placeholder={isSecret ? "***" : ""}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          );
        })}
        {Object.keys(schema).length === 0 && (
           <p className="text-yellow-400 mb-4 text-sm">No manifest schema found. Falling back to key-value editor.</p>
        )}
        <div className="flex gap-4">
          <button type="button" onClick={handleAdd} className="bg-gray-600 px-6 py-2 rounded text-white hover:bg-gray-700">Add Key</button>
          <button type="submit" className="bg-blue-600 px-6 py-2 rounded text-white font-bold hover:bg-blue-700">Save</button>
        </div>
      </form>
    </div>
  );
}
