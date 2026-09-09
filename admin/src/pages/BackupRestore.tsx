import { useState } from 'react';
import axios from 'axios';

export function BackupRestore() {
  const [msg, setMsg] = useState('');

  const handleBackup = async () => {
    try {
      const res = await axios.post('/api/system/backup', {}, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }});
      setMsg(`Backup created: ${res.data.file}`);
    } catch(e: any) {
      setMsg(`Backup failed: ${e.response?.data?.detail}`);
    }
  };

  const handleRestore = async () => {
    try {
      await axios.post('/api/system/restore', {}, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }});
      setMsg("System restored successfully.");
    } catch(e: any) {
      setMsg(`Restore failed: ${e.response?.data?.detail}`);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Backup & Restore</h1>
      {msg && <div className="mb-4 text-yellow-400">{msg}</div>}
      <div className="flex gap-4">
        <button onClick={handleBackup} className="bg-blue-600 px-4 py-2 rounded font-bold hover:bg-blue-700">Create Backup</button>
        <button onClick={handleRestore} className="bg-red-600 px-4 py-2 rounded font-bold hover:bg-red-700">Restore Default / Mock</button>
      </div>
    </div>
  );
}
