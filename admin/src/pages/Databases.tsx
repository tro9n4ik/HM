import { Database, Construction } from 'lucide-react';

export function Databases() {
  return (
    <div className="p-8 max-w-6xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex items-center text-sm text-gray-500 mb-6 flex-shrink-0">
        <span>Система <span className="text-gray-300 mx-2">/</span> Базы данных</span>
      </div>

      <div className="bg-white p-12 border border-gray-200 rounded-lg shadow-sm flex flex-col flex-1 items-center justify-center text-center">
        <div className="bg-gray-50 p-6 rounded-full border border-gray-100 mb-6 relative">
          <Database className="w-16 h-16 text-gray-300" />
          <div className="absolute -bottom-2 -right-2 bg-emerald-100 p-2 rounded-full border border-emerald-200">
             <Construction className="w-6 h-6 text-emerald-600" />
          </div>
        </div>

        <h1 className="text-2xl font-bold mb-3 text-gray-800">Функция в разработке</h1>
        <p className="text-gray-500 max-w-md mx-auto mb-8">
          Этот раздел будет предназначен для управления встроенными базами данных плагинов и просмотра системной схемы ядра. Следите за обновлениями!
        </p>

        <button className="bg-white border border-gray-300 text-gray-700 px-6 py-2.5 rounded-md font-medium text-sm cursor-not-allowed opacity-50">
          Подключить БД
        </button>
      </div>
    </div>
  );
}
