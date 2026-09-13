import axios from 'axios';

export type ToastHandler = (message: string, type: 'error' | 'warning') => void;
let notify: ToastHandler = () => {};
export const setToastHandler = (handler: ToastHandler) => { notify = handler; };

let interceptorRegistered = false;
export function registerApiInterceptors() {
  if (interceptorRegistered) return;
  interceptorRegistered = true;

  axios.interceptors.response.use(
    response => response,
    error => {
      if (!error.response) {
        notify('Нет связи с сервером. Проверьте соединение.', 'error');
      } else if (error.response.status === 401) {
        if (window.location.pathname !== '/login' && window.location.pathname !== '/setup') {
          window.location.href = '/login';
        }
      } else if (error.response.status === 502 || error.response.status === 503) {
        notify('Сервер временно недоступен. Повторите попытку позже.', 'warning');
      }
      return Promise.reject(error);
    }
  );
}
