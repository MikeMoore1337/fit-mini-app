const accessTokenKey = 'fit_access_token';
const refreshTokenKey = 'fit_refresh_token';

const state = {
  me: null,
  exercises: [],
  templates: [],
};

const API = {
  telegramInit: '/api/v1/auth/telegram/init',
  me: '/api/v1/me',
  meProfile: '/api/v1/me/profile',

  exercises: '/api/v1/programs/exercises',
  saveTemplate: '/api/v1/programs/templates',
  myTemplates: '/api/v1/programs/templates/mine',
  deleteTemplate: (id) => `/api/v1/programs/templates/${id}`,

  notifications: '/api/v1/notifications',
  deleteNotification: (id) => `/api/v1/notifications/${id}`,
};

const $ = (id) => document.getElementById(id);

function authHeaders() {
  const token = localStorage.getItem(accessTokenKey);
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: authHeaders(),
  });

  const text = await res.text();

  if (!res.ok) {
    console.error(path, text);
    throw new Error(text);
  }

  return text ? JSON.parse(text) : null;
}

function showToast(msg) {
  console.log(msg);
}

async function loadTemplates() {
  state.templates = await api(API.myTemplates);

  const list = $('templatesList');
  if (!list) return;

  list.innerHTML =
    state.templates
      .map(
        (t) => `
        <div class="item-card">
          <strong>${t.title}</strong>
          <div>${t.goal} - ${t.level}</div>
          <button class="delete-template" data-id="${t.id}">
            Удалить
          </button>
        </div>
      `
      )
      .join('') || 'Нет шаблонов';

  document.querySelectorAll('.delete-template').forEach((btn) => {
    btn.onclick = async () => {
      if (!confirm('Удалить шаблон?')) return;

      await api(API.deleteTemplate(btn.dataset.id), {
        method: 'DELETE',
      });

      showToast('Удалено');
      loadTemplates();
    };
  });
}

async function loadNotifications() {
  const data = await api(API.notifications);

  const list = $('notificationsList');
  if (!list) return;

  list.innerHTML =
    data
      .map(
        (n) => `
        <div class="item-card">
          <strong>${n.title}</strong>
          <div>${n.body}</div>
          <button class="delete-notif" data-id="${n.id}">
            Удалить
          </button>
        </div>
      `
      )
      .join('') || 'Нет уведомлений';

  document.querySelectorAll('.delete-notif').forEach((btn) => {
    btn.onclick = async () => {
      if (!confirm('Удалить напоминание?')) return;

      await api(API.deleteNotification(btn.dataset.id), {
        method: 'DELETE',
      });

      showToast('Удалено');
      loadNotifications();
    };
  });
}

async function init() {
  try {
    await loadTemplates();
    await loadNotifications();
  } catch (e) {
    console.error(e);
  }
}

document.addEventListener('DOMContentLoaded', init);