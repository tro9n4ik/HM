import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface SetupProps {
  onSetupComplete?: () => void;
}

export function Setup({ onSetupComplete }: SetupProps) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('/api/auth/setup', { username, password });
      if (onSetupComplete) {
        onSetupComplete();
      }
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Setup failed');
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-900 text-white">
      <form onSubmit={handleSetup} className="bg-gray-800 p-8 rounded-lg shadow-lg w-96">
        <h2 className="text-2xl font-bold mb-6">Home.Media Setup</h2>
        {error && <div className="text-red-500 mb-4">{error}</div>}
        <div className="mb-4">
          <label className="block mb-2">Admin Username</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        <div className="mb-6">
          <label htmlFor="password-input" className="block mb-2">Password</label>
          <input
            id="password-input"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 p-2 rounded font-bold">
          Create Admin Account
        </button>
      </form>
    </div>
  );
}
