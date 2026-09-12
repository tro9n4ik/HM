import { useEffect, useState } from 'react';
import axios from 'axios';
import { ScrollText } from 'lucide-react';

export function Logs() {
  const [activities, setActivities] = useState<any[]>([]);

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const activityRes = await axios.get('/api/system/activity?limit=100').catch(() => null);
        if (activityRes?.data) setActivities(activityRes.data);
      } catch (e) {
        console.error(e);
      }
    };

    fetchActivities();
    const interval = setInterval(fetchActivities, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center text-sm text-gray-500 mb-6">
        <span>Система <span className="text-gray-300 mx-2">/</span> Логи</span>
      </div>

      <div className="bg-white p-8 border border-gray-200 rounded-lg shadow-sm">
        <h1 className="text-2xl font-bold mb-6 text-gray-800 flex items-center gap-2">
          <ScrollText className="w-6 h-6 text-gray-400" />
          Системные логи
        </h1>

        <div className="space-y-4">
            {activities.length > 0 ? activities.map((act, i) => (
              <div key={i} className="flex justify-between text-sm pb-3 border-b border-gray-50 last:border-0 last:pb-0 hover:bg-gray-50/50 p-2 -mx-2 rounded">
                <div className="flex gap-6">
                  <span className="text-gray-400 font-mono text-xs w-16 mt-0.5">{act.time}</span>
                  <span className="text-gray-700">{act.message}</span>
                </div>
                <span className="text-gray-400 text-xs px-2 py-0.5 bg-gray-100 rounded border border-gray-200">{act.source}</span>
              </div>
            )) : (
              <div className="text-sm text-gray-500 italic py-4">Нет системной активности для отображения</div>
            )}
        </div>
      </div>
    </div>
  );
}
