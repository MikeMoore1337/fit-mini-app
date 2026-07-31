import { initTelegramTheme } from '/static/js/core/theme.js?v=57';
import { openConfirmDialog } from '/static/js/core/ui.js?v=57';

    initTelegramTheme({
      onError: (error) => console.warn(`Telegram theme: ${String(error)}`),
    });

    const accessTokenKey = 'fit_access_token';
    const legacyToken = localStorage.getItem(accessTokenKey);
    if (legacyToken && !sessionStorage.getItem(accessTokenKey)) {
      sessionStorage.setItem(accessTokenKey, legacyToken);
    }
    localStorage.removeItem(accessTokenKey);
    localStorage.removeItem('fit_refresh_token');
    let adminUsers = [];
    let adminUsersTotal = 0;
    let adminUsersPage = 1;
    const adminUsersPageSize = 10;
    let adminUserSearchTimer = null;
    const adminCollectionPageSize = 20;
    const adminCollectionPages = {
      payments: { page: 1, total: 0 },
      notifications: { page: 1, total: 0 },
      templates: { page: 1, total: 0 },
    };

    const $ = (id) => document.getElementById(id);

    function log(msg) {
      const node = $('adminLog');
      if (!node) return;
      const text = typeof msg === 'string' ? msg : JSON.stringify(msg, null, 2);
      node.textContent = `${new Date().toLocaleTimeString()} · ${text}\n${node.textContent}`;
    }

    function showToast(message, type = 'success') {
      const toast = $('toast');
      if (!toast) return;

      toast.textContent = message;
      toast.className = `toast ${type === 'error' ? 'error' : ''}`.trim();

      setTimeout(() => {
        toast.className = 'toast hidden';
      }, 2500);
    }

    function escapeHtml(value) {
      const text = value == null ? '' : String(value);
      const replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
      };
      return text.replace(/[&<>"']/g, (char) => replacements[char]);
    }

    function getRoleLabel(user) {
      if (user?.is_admin) return 'Администратор';
      if (user?.is_coach) return 'Тренер';
      return 'Клиент';
    }

    function getRoleValue(user) {
      return user?.role || (user?.is_admin ? 'admin' : user?.is_coach ? 'coach' : 'client');
    }

    function getRoleValueLabel(value) {
      return ({ client: 'Клиент', coach: 'Тренер', admin: 'Администратор' }[value] || value);
    }

    function getGoalLabel(goal) {
      return ({
        fat_loss: 'Похудение',
        muscle_gain: 'Набор',
        maintenance: 'Поддержание',
        recomposition: 'Рекомпозиция',
      }[goal] || goal || '-');
    }

    function getLevelLabel(level) {
      return ({
        beginner: 'Начальный',
        intermediate: 'Средний',
        advanced: 'Продвинутый',
      }[level] || level || '-');
    }

    function getPaymentStatusLabel(status) {
      return ({
        created: 'Создан',
        paid: 'Оплачен',
        failed: 'Ошибка',
      }[status] || status || '-');
    }

    function getNotificationStatusLabel(status) {
      return ({
        queued: 'Ожидает',
        sent: 'Отправлено',
        failed: 'Ошибка',
      }[status] || status || '-');
    }

    function formatDateTimeInZone(value, timezone = 'Europe/Moscow') {
      if (!value) return '';
      const raw = String(value);
      const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/.test(raw);
      if (!hasTimezone) {
        const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
        if (match) {
          const [, year, month, day, hour, minute] = match;
          return `${day}.${month}.${year}, ${hour}:${minute}`;
        }
      }

      const date = new Date(raw);
      if (Number.isNaN(date.getTime())) return raw;

      return new Intl.DateTimeFormat('ru-RU', {
        timeZone: timezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date);
    }

    function roleOption(value, label, current) {
      return `<option value="${value}" ${current === value ? 'selected' : ''}>${label}</option>`;
    }

    function authHeaders() {
      const token = sessionStorage.getItem(accessTokenKey);
      return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
    }

    async function refreshAccessToken() {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!response.ok) return false;
      const data = await response.json();
      sessionStorage.setItem(accessTokenKey, data.access_token);
      return true;
    }

    async function api(path, options = {}, allowRefresh = true) {
      const { includeMeta = false, ...fetchOptions } = options;
      const res = await fetch(path, {
        ...fetchOptions,
        credentials: 'same-origin',
        headers: {
          ...authHeaders(),
          ...(fetchOptions.headers || {}),
        },
      });
      if (res.status === 401 && allowRefresh && await refreshAccessToken()) {
        return api(path, options, false);
      }
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
      }
      if (res.status === 204) {
        return null;
      }
      const data = await res.json();
      if (includeMeta) {
        return { items: data, total: Number(res.headers.get('X-Total-Count') || data.length) };
      }
      return data;
    }

    async function ensureAdminAccess() {
      const me = await api('/api/v1/me');
      if (!me.is_admin) throw new Error('Недостаточно прав администратора');
    }

    function renderUsers() {
      const pageCount = Math.max(1, Math.ceil(adminUsersTotal / adminUsersPageSize));
      adminUsersPage = Math.min(adminUsersPage, pageCount);
      const rows = adminUsers;
      $('usersList').innerHTML = rows.map(user => `
        <div class="item-card">
          <strong>${escapeHtml(user.full_name || user.telegram_user_id)}</strong><br>
          <span class="muted">
            № ${escapeHtml(user.telegram_user_id)} ·
            ${escapeHtml(getRoleLabel(user))} ·
            ${user.is_active ? 'Активен' : 'Заблокирован'}
          </span>
          <details class="admin-actions top-gap">
            <summary>Управление пользователем</summary>
            <div class="admin-actions__body">
              <label class="field"><span>Роль</span><select class="user-role-select" data-user-id="${escapeHtml(user.id)}">
                ${roleOption('client', 'Клиент', getRoleValue(user))}
                ${roleOption('coach', 'Тренер', getRoleValue(user))}
                ${roleOption('admin', 'Администратор', getRoleValue(user))}
              </select></label>
              <div class="toolbar wrap">
                <button class="secondary save-user-role-btn" type="button" data-user-id="${escapeHtml(user.id)}" data-current-role="${escapeHtml(getRoleValue(user))}" data-user-name="${escapeHtml(user.full_name || user.telegram_user_id)}">Сохранить роль</button>
                <button class="secondary user-status-btn" type="button" data-user-id="${escapeHtml(user.id)}" data-user-name="${escapeHtml(user.full_name || user.telegram_user_id)}" data-next-active="${user.is_active ? 'false' : 'true'}">${user.is_active ? 'Заблокировать' : 'Разблокировать'}</button>
                <button class="secondary danger-text delete-user-btn" type="button" data-user-id="${escapeHtml(user.id)}" data-user-name="${escapeHtml(user.full_name || user.telegram_user_id)}">Удалить аккаунт</button>
              </div>
            </div>
          </details>
        </div>
      `).join('') || '<p class="muted">Пользователей нет</p>';

      document.querySelectorAll('.save-user-role-btn').forEach(button => {
        button.onclick = async () => {
          const select = document.querySelector(`.user-role-select[data-user-id="${button.dataset.userId}"]`);
          if (!select || select.value === button.dataset.currentRole) return;
          const confirmed = await openConfirmDialog({
            title: 'Изменить роль пользователя?',
            message: `${button.dataset.userName}: новая роль — ${getRoleValueLabel(select.value)}. Права доступа изменятся сразу.`,
            okText: 'Изменить роль',
            danger: select.value === 'admin' || button.dataset.currentRole === 'admin',
          });
          if (!confirmed) return;
          try {
            await api(`/api/v1/admin/users/${select.dataset.userId}/role`, {
              method: 'PATCH',
              body: JSON.stringify({ role: select.value }),
            });
            showToast('Роль обновлена');
            await loadUsers();
          } catch (error) {
            log(String(error));
            showToast('Не удалось обновить роль', 'error');
            await loadUsers();
          }
        };
      });

      document.querySelectorAll('.user-status-btn').forEach(button => {
        button.onclick = async () => {
          const nextActive = button.dataset.nextActive === 'true';
          const confirmed = await openConfirmDialog({
            title: nextActive ? 'Разблокировать пользователя?' : 'Заблокировать пользователя?',
            message: nextActive ? `${button.dataset.userName} снова получит доступ к приложению.` : `${button.dataset.userName} потеряет доступ до ручной разблокировки.`,
            okText: nextActive ? 'Разблокировать' : 'Заблокировать',
            danger: !nextActive,
          });
          if (!confirmed) return;
          try {
            await api(`/api/v1/admin/users/${button.dataset.userId}/status`, {
              method: 'PATCH',
              body: JSON.stringify({ is_active: nextActive }),
            });
            showToast(nextActive ? 'Пользователь разблокирован' : 'Пользователь заблокирован');
            await loadUsers();
          } catch (error) {
            log(String(error));
            showToast('Не удалось изменить статус пользователя', 'error');
          }
        };
      });

      document.querySelectorAll('.delete-user-btn').forEach(button => {
        button.onclick = async () => {
          const name = button.dataset.userName || 'пользователя';
          const confirmed = await openConfirmDialog({
            title: `Удалить ${name}?`,
            message: 'Связанные тренировки, уведомления и платежи будут удалены без возможности восстановления.',
            okText: 'Удалить аккаунт',
            danger: true,
          });
          if (!confirmed) return;

          try {
            await api(`/api/v1/admin/users/${button.dataset.userId}`, {
              method: 'DELETE',
            });
            showToast('Пользователь удалён');
            await loadUsers();
          } catch (error) {
            log(String(error));
            showToast('Не удалось удалить пользователя', 'error');
          }
        };
      });

      $('usersPagination').innerHTML = pageCount > 1 ? `
        <button id="usersPrevPage" class="secondary" type="button" ${adminUsersPage === 1 ? 'disabled' : ''}>Назад</button>
        <span class="muted">${adminUsersPage} из ${pageCount} · найдено ${adminUsersTotal}</span>
        <button id="usersNextPage" class="secondary" type="button" ${adminUsersPage === pageCount ? 'disabled' : ''}>Далее</button>
      ` : `<span class="muted">Найдено: ${adminUsersTotal}</span>`;
      if ($('usersPrevPage')) $('usersPrevPage').onclick = async () => { adminUsersPage -= 1; await loadUsers(true); };
      if ($('usersNextPage')) $('usersNextPage').onclick = async () => { adminUsersPage += 1; await loadUsers(true); };
    }

    async function loadUsers(silent = false) {
      const params = new URLSearchParams({
        limit: String(adminUsersPageSize),
        offset: String((adminUsersPage - 1) * adminUsersPageSize),
      });
      const search = $('adminUserSearch').value.trim();
      const role = $('adminRoleFilter').value;
      const userStatus = $('adminStatusFilter').value;
      if (search) params.set('search', search);
      if (role) params.set('role', role);
      if (userStatus) params.set('active', userStatus === 'active' ? 'true' : 'false');
      const result = await api(`/api/v1/admin/users?${params}`, { includeMeta: true });
      adminUsers = result.items;
      adminUsersTotal = result.total;
      renderUsers();

      if (!silent) showToast('Пользователи загружены');
    }

    function renderCollectionPagination(containerId, key, loadPage) {
      const pagination = adminCollectionPages[key];
      const pageCount = Math.max(1, Math.ceil(pagination.total / adminCollectionPageSize));
      pagination.page = Math.min(pagination.page, pageCount);
      const previousId = `${key}PrevPage`;
      const nextId = `${key}NextPage`;
      $(containerId).innerHTML = pageCount > 1 ? `
        <button id="${previousId}" class="secondary" type="button" ${pagination.page === 1 ? 'disabled' : ''}>Назад</button>
        <span class="muted">${pagination.page} из ${pageCount} · всего ${pagination.total}</span>
        <button id="${nextId}" class="secondary" type="button" ${pagination.page === pageCount ? 'disabled' : ''}>Далее</button>
      ` : `<span class="muted">Всего: ${pagination.total}</span>`;
      if ($(previousId)) $(previousId).onclick = async () => {
        pagination.page -= 1;
        await loadPage(true);
      };
      if ($(nextId)) $(nextId).onclick = async () => {
        pagination.page += 1;
        await loadPage(true);
      };
    }

    function collectionParams(key) {
      const pagination = adminCollectionPages[key];
      return new URLSearchParams({
        limit: String(adminCollectionPageSize),
        offset: String((pagination.page - 1) * adminCollectionPageSize),
      });
    }

    async function loadPayments(silent = false) {
      const result = await api(`/api/v1/admin/payments?${collectionParams('payments')}`, { includeMeta: true });
      const rows = result.items;
      adminCollectionPages.payments.total = result.total;
      $('paymentsList').innerHTML = rows.map(row => `
        <div class="item-card">
          <strong>${escapeHtml(row.plan_title || row.plan_code)}</strong><br>
          <span class="muted">
            Пользователь: ${escapeHtml(row.telegram_user_id)} |
            Статус: ${escapeHtml(getPaymentStatusLabel(row.status))} |
            ${escapeHtml(row.amount)} ${escapeHtml(row.currency)}
          </span>
        </div>
      `).join('') || '<p class="muted">Платежей нет</p>';
      renderCollectionPagination('paymentsPagination', 'payments', loadPayments);
      if (!silent) showToast('Платежи загружены');
    }

    async function loadNotifications(silent = false) {
      const result = await api(`/api/v1/admin/notifications?${collectionParams('notifications')}`, { includeMeta: true });
      const rows = result.items;
      adminCollectionPages.notifications.total = result.total;
      $('adminNotificationsList').innerHTML = rows.map(row => `
        <div class="item-card">
          <strong>${escapeHtml(row.title)}</strong><br>
          <span class="muted">${escapeHtml(formatDateTimeInZone(row.scheduled_for, row.timezone))} ${escapeHtml(row.timezone || 'Europe/Moscow')} · ${escapeHtml(getNotificationStatusLabel(row.status))}</span>
          <div>${escapeHtml(row.body)}</div>
        </div>
      `).join('') || '<p class="muted">Уведомлений нет</p>';
      renderCollectionPagination('notificationsPagination', 'notifications', loadNotifications);
      if (!silent) showToast('Уведомления загружены');
    }

    async function loadTemplates(silent = false) {
      const result = await api(`/api/v1/admin/templates?${collectionParams('templates')}`, { includeMeta: true });
      const rows = result.items;
      adminCollectionPages.templates.total = result.total;
      if (!rows.length && adminCollectionPages.templates.page > 1) {
        adminCollectionPages.templates.page -= 1;
        return loadTemplates(silent);
      }
      $('adminTemplatesList').innerHTML = rows.map(row => `
        <div class="item-card">
          <strong>${escapeHtml(row.title)}</strong><br>
          <span class="muted">${escapeHtml(getGoalLabel(row.goal))} · ${escapeHtml(getLevelLabel(row.level))}</span>
          <div class="toolbar wrap top-gap">
            <button
              class="btn-danger delete-template-btn"
              type="button"
              data-template-id="${escapeHtml(row.id)}"
              data-template-title="${escapeHtml(row.title)}"
            >
              Удалить
            </button>
          </div>
        </div>
      `).join('') || '<p class="muted">Шаблонов нет</p>';

      document.querySelectorAll('.delete-template-btn').forEach(button => {
        button.onclick = async () => {
          const title = button.dataset.templateTitle || 'шаблон';
          const confirmed = await openConfirmDialog({
            title: `Удалить шаблон «${title}»?`,
            message: 'Шаблон будет удалён, но уже назначенные программы и история тренировок сохранятся.',
            okText: 'Удалить шаблон',
            danger: true,
          });
          if (!confirmed) return;

          try {
            await api(`/api/v1/admin/templates/${button.dataset.templateId}`, {
              method: 'DELETE',
            });
            showToast('Шаблон удалён');
            await loadTemplates();
          } catch (error) {
            log(String(error));
            showToast('Не удалось удалить шаблон', 'error');
          }
        };
      });

      renderCollectionPagination('templatesPagination', 'templates', loadTemplates);
      if (!silent) showToast('Шаблоны загружены');
    }

    async function withLoading(button, action, successText, errorText) {
      const original = button.textContent;
      try {
        button.disabled = true;
        button.textContent = 'Загрузка…';
        await action();
        if (successText) showToast(successText);
      } catch (error) {
        log(String(error));
        showToast(errorText || 'Ошибка', 'error');
      } finally {
        button.disabled = false;
        button.textContent = original;
      }
    }

    $('loadUsersBtn').onclick = (e) =>
      withLoading(e.currentTarget, loadUsers, null, 'Не удалось загрузить пользователей');

    $('loadPaymentsBtn').onclick = (e) =>
      withLoading(e.currentTarget, loadPayments, null, 'Не удалось загрузить платежи');

    $('loadNotificationsBtn').onclick = (e) =>
      withLoading(e.currentTarget, loadNotifications, null, 'Не удалось загрузить уведомления');

    $('loadTemplatesBtn').onclick = (e) =>
      withLoading(e.currentTarget, loadTemplates, null, 'Не удалось загрузить шаблоны');

    ['adminRoleFilter', 'adminStatusFilter'].forEach((id) => {
      $(id).addEventListener('change', async () => {
        adminUsersPage = 1;
        await loadUsers(true);
      });
    });
    $('adminUserSearch').addEventListener('input', () => {
      clearTimeout(adminUserSearchTimer);
      adminUserSearchTimer = setTimeout(async () => {
        adminUsersPage = 1;
        await loadUsers(true);
      }, 300);
    });

    if (new URLSearchParams(location.search).get('debug') === '1') {
      $('adminDiagnosticCard').classList.remove('hidden');
    }

    (async () => {
      try {
        await ensureAdminAccess();
      } catch (error) {
        $('usersList').innerHTML = '<div class="empty-state"><p class="empty-state__title">Недостаточно прав администратора</p><p class="empty-state__text muted">Вернитесь в Mini App под аккаунтом администратора.</p></div>';
        showToast('Недостаточно прав администратора', 'error');
        return;
      }
      const results = await Promise.allSettled([
        loadUsers(true),
        loadPayments(true),
        loadNotifications(true),
        loadTemplates(true),
      ]);
      if (results.some((result) => result.status === 'rejected')) {
        showToast('Часть данных не загрузилась. Используйте «Обновить» в нужном разделе.', 'error');
      }
    })();
