import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UserPlus } from 'lucide-react';

interface SetupProps {
  onSetupComplete?: () => void;
}

export function Setup({ onSetupComplete }: SetupProps) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await axios.post('/api/auth/setup', { username, password });
      if (onSetupComplete) {
        onSetupComplete();
      }
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка настройки');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50 text-gray-900 font-sans">
      <form onSubmit={handleSetup} className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 w-96">
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-gray-900 text-white p-1.5 rounded">
            <span className="font-bold text-sm">HM</span>
          </div>
          <h2 className="text-xl font-bold text-gray-800">Первоначальная настройка</h2>
        </div>

        {error && (
          <div className="text-red-500 mb-4 text-sm bg-red-50 border border-red-200 p-3 rounded">
            {error}
          </div>
        )}

        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium text-gray-700">Имя администратора</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="w-full p-2.5 rounded-md bg-white border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 disabled:opacity-50 disabled:bg-gray-50 transition-all text-sm"
            required
            disabled={isLoading}
          />
        </div>

        <div className="mb-6">
          <label htmlFor="password-input" className="block mb-2 text-sm font-medium text-gray-700">Пароль</label>
          <input
            id="password-input"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full p-2.5 rounded-md bg-white border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 disabled:opacity-50 disabled:bg-gray-50 transition-all text-sm"
            required
            disabled={isLoading}
            placeholder="••••••••"
          />
        </div>

        <button
          type="submit"
          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white p-2.5 rounded-md font-medium disabled:opacity-70 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 text-sm"
          disabled={isLoading}
        >
          {isLoading ? (
            <span>Создание...</span>
          ) : (
            <>
              <UserPlus className="w-4 h-4" />
              Создать аккаунт
            </>
          )}
        </button>
      </form>
    </div>
  );
}
