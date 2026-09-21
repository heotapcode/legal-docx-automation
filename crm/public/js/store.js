/**
 * store.js - Client-side state management (localStorage)
 */
window.CRM = window.CRM || {};

CRM.Store = (() => {
  const TOKEN_KEY = 'crm_token';
  const USER_KEY = 'crm_user';

  return {
    getToken() { return localStorage.getItem(TOKEN_KEY); },
    setToken(token) { localStorage.setItem(TOKEN_KEY, token); },
    removeToken() { localStorage.removeItem(TOKEN_KEY); },

    getUser() {
      try { return JSON.parse(localStorage.getItem(USER_KEY)); }
      catch { return null; }
    },
    setUser(user) { localStorage.setItem(USER_KEY, JSON.stringify(user)); },
    removeUser() { localStorage.removeItem(USER_KEY); },

    isLoggedIn() { return !!this.getToken() && !!this.getUser(); },
    isAdmin() { const u = this.getUser(); return u && u.role === 'admin'; }
  };
})();
