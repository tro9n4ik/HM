import { useState } from 'react';
import axios from 'axios';

export function BackupRestore() {
  const [msg, setMsg] = useState('');

  const handleBackup = async () => {
    try {
      await axios.post('/api/system/backup');
      setMsg(`Backup created: hm_backup.json (Check server temp dir)`);
    } catch(e: any) {
      setMsg(`Backup failed: ${e.response?.data?.detail}`);
    }
  };

  const handleRestore = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      try {
        const formData = new FormData();
        formData.append('file', e.target.files[0]);
        await axios.post('/api/system/restore', formData);
        setMsg("System restored successfully.");
      } catch(e: any) {
        setMsg(`Restore failed: ${e.response?.data?.detail}`);
      }
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Backup & Restore</h1>
      {msg && <div className="mb-4 text-yellow-400">{msg}</div>}
      <div className="flex gap-4 items-center">
        <button onClick={handleBackup} className="bg-blue-600 px-4 py-2 rounded font-bold hover:bg-blue-700">Create Backup</button>
        <span className="text-gray-400">or</span>
        <label className="bg-red-600 px-4 py-2 rounded font-bold hover:bg-red-700 cursor-pointer">
          Restore from File
          <input type="file" className="hidden" accept=".json" onChange={handleRestore} />
        </label>
      </div>
    </div>
  );
}
