/**
 * api.js - HTTP Client cho NAC CRM
 */
window.CRM = window.CRM || {};

CRM.API = (() => {
  const BASE = '';

  async function request(method, url, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };

    const token = CRM.Store.getToken();
    if (token) {
      opts.headers['Authorization'] = `Bearer ${token}`;
    }

    if (body && method !== 'GET') {
      opts.body = JSON.stringify(body);
    }

    try {
      const res = await fetch(BASE + url, opts);
      const data = await res.json();

      if (res.status === 401) {
        CRM.Store.removeToken();
        CRM.Store.removeUser();
        CRM.Auth.renderLogin();
        throw new Error('Phiên đăng nhập hết hạn');
      }

      if (!res.ok || !data.success) {
        throw new Error(data.message || `Lỗi ${res.status}`);
      }

      return data;
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        throw new Error('Không thể kết nối server. Vui lòng kiểm tra kết nối.');
      }
      throw err;
    }
  }

  return {
    get: (url) => request('GET', url),
    post: (url, body) => request('POST', url, body),
    put: (url, body) => request('PUT', url, body),
    delete: (url) => request('DELETE', url)
  };
})();
