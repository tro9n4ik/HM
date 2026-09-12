import { useState } from 'react';
import axios from 'axios';
import { Download, Upload } from 'lucide-react';

export function BackupRestore() {
  const [msg, setMsg] = useState('');
  const [isError, setIsError] = useState(false);

  const handleBackup = async () => {
    try {
      const response = await axios.post('/api/system/backup', {}, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'hm_backup.json');
      document.body.appendChild(link);
      link.click();

      setMsg(`Резервная копия успешно создана и скачана`);
      setIsError(false);
    } catch(e: any) {
      setMsg(`Ошибка создания копии: ${e.response?.data?.detail || e.message}`);
      setIsError(true);
    }
  };

  const handleRestore = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      try {
        const formData = new FormData();
        formData.append('file', e.target.files[0]);
        await axios.post('/api/system/restore', formData);
        setMsg("Система успешно восстановлена.");
        setIsError(false);
      } catch(e: any) {
        setMsg(`Ошибка восстановления: ${e.response?.data?.detail || e.message}`);
        setIsError(true);
      }
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center text-sm text-gray-500 mb-6">
        <span>Настройки <span className="text-gray-300 mx-2">/</span> Резервное копирование</span>
      </div>

      <div className="bg-white p-8 border border-gray-200 rounded-lg shadow-sm">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">Резервное копирование и восстановление</h1>

        {msg && (
          <div className={`mb-6 px-4 py-3 rounded text-sm ${isError ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-emerald-50 text-emerald-600 border border-emerald-200'}`}>
            {msg}
          </div>
        )}

        <div className="flex gap-4 items-center mt-8">
          <button
            onClick={handleBackup}
            className="flex items-center gap-2 bg-emerald-600 px-5 py-2.5 rounded-md font-medium text-white hover:bg-emerald-700 transition-colors text-sm"
          >
            <Download className="w-4 h-4" />
            Создать бэкап
          </button>

          <span className="text-gray-400 text-sm">или</span>

          <label className="flex items-center gap-2 bg-white px-5 py-2.5 border border-gray-300 rounded-md font-medium text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors text-sm">
            <Upload className="w-4 h-4 text-gray-500" />
            Восстановить из файла
            <input type="file" className="hidden" accept=".json" onChange={handleRestore} />
          </label>
        </div>
        <p className="mt-6 text-xs text-gray-500">
          При создании резервной копии все пароли и секретные ключи плагинов автоматически исключаются в целях безопасности.
        </p>
      </div>
    </div>
  );
}
