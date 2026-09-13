import React from 'react';

interface PluginInstallCardProps {
    fileName: string;
    state: 'idle' | 'uploading' | 'installing' | 'done' | 'error';
    error?: string;
}

const PluginInstallCard: React.FC<PluginInstallCardProps> = ({ fileName, state, error }) => {
    if (state === 'idle') return null;

    let icon = null;
    let text = '';
    let bgColor = 'bg-white';
    let borderColor = 'border-gray-200';
    let textColor = 'text-gray-800';

    if (state === 'uploading' || state === 'installing') {
        text = state === 'uploading' ? 'Загрузка архива...' : 'Установка зависимостей...';
        icon = (
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        );
    } else if (state === 'done') {
        text = 'Плагин успешно установлен';
        bgColor = 'bg-emerald-50';
        borderColor = 'border-emerald-200';
        textColor = 'text-emerald-700';
        icon = (
            <svg className="w-5 h-5 mr-3 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
        );
    } else if (state === 'error') {
        text = error || 'Ошибка установки';
        bgColor = 'bg-red-50';
        borderColor = 'border-red-200';
        textColor = 'text-red-700';
        icon = (
            <svg className="w-5 h-5 mr-3 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        );
    }

    return (
        <div className={`fixed bottom-6 right-6 z-50 transform transition-all duration-300 translate-y-0 opacity-100 flex items-center p-4 rounded-lg border shadow-lg ${bgColor} ${borderColor} max-w-sm w-full`}>
            {icon}
            <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium truncate ${textColor}`}>
                    {text}
                </p>
                <p className={`text-xs truncate ${state === 'error' ? 'text-red-500' : 'text-gray-500'}`}>
                    {fileName}
                </p>
            </div>
        </div>
    );
};

export default PluginInstallCard;
