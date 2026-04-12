import { sectionStoragePrefix } from './config.js';

export function $(id) {
  return document.getElementById(id);
}

export function log(message) {
  const node = $('log');
  if (!node) return;
  const text = typeof message === 'string' ? message : JSON.stringify(message, null, 2);
  node.textContent = `${new Date().toLocaleTimeString()} - ${text}\n${node.textContent}`;
}

export function showToast(message, type = 'success') {
  const toast = $('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast${type === 'error' ? ' error' : ''}`;
  toast.removeAttribute('aria-hidden');
  setTimeout(() => {
    toast.className = 'toast hidden';
    toast.setAttribute('aria-hidden', 'true');
  }, 2800);
}

/** Сообщение об ошибке из исключения API (поле message уже заполняется в http.js). */
export function toastError(error, fallback) {
  const raw = error && error.message != null ? String(error.message).trim() : '';
  showToast(raw || fallback, 'error');
}

export function setAppLoading(active) {
  const el = $('globalLoading');
  if (!el) return;
  el.classList.toggle('hidden', !active);
  el.setAttribute('aria-hidden', active ? 'false' : 'true');
  el.setAttribute('aria-busy', active ? 'true' : 'false');
  document.body.classList.toggle('app-loading', active);
}

export function expandSectionAndScroll(sectionContentId, cardId) {
  const body = document.getElementById(sectionContentId);
  const btn = document.querySelector(`.section-toggle[data-target="${sectionContentId}"]`);
  if (body && btn) {
    body.classList.remove('hidden');
    btn.textContent = 'Свернуть';
    try {
      localStorage.setItem(`${sectionStoragePrefix}${sectionContentId}`, 'expanded');
    } catch {
      /* ignore */
    }
  }
  const card = document.getElementById(cardId);
  if (card) {
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/**
 * @param {{ title: string, message: string, okText?: string, danger?: boolean }} opts
 * @returns {Promise<boolean>}
 */
export function openConfirmDialog({ title, message, okText = 'Подтвердить', danger = true }) {
  return new Promise((resolve) => {
    const root = $('confirmModal');
    if (!root) {
      resolve(false);
      return;
    }

    const titleEl = $('confirmModalTitle');
    const bodyEl = $('confirmModalBody');
    const okBtn = $('confirmModalOk');
    const cancelBtn = $('confirmModalCancel');
    const backdrop = root.querySelector('.modal__backdrop');

    if (!titleEl || !bodyEl || !okBtn || !cancelBtn) {
      resolve(false);
      return;
    }

    titleEl.textContent = title;
    bodyEl.textContent = message;
    okBtn.textContent = okText;
    okBtn.classList.remove('btn-danger');
    if (danger) okBtn.classList.add('btn-danger');

    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      root.classList.add('hidden');
      root.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      document.removeEventListener('keydown', onKey);
      resolve(value);
    };

    const onKey = (e) => {
      if (e.key === 'Escape') finish(false);
    };

    const onOk = () => finish(true);
    const onCancel = () => finish(false);

    okBtn.onclick = onOk;
    cancelBtn.onclick = onCancel;
    if (backdrop) backdrop.onclick = onCancel;
    document.addEventListener('keydown', onKey);

    root.classList.remove('hidden');
    root.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    requestAnimationFrame(() => cancelBtn.focus());
  });
}

export function bindGlobalNavHandlers() {
  document.body.addEventListener('click', (e) => {
    const t = e.target.closest('.empty-state-goto, .app-bottom-nav__btn');
    if (!t) return;
    const section = t.getAttribute('data-nav-section');
    const card = t.getAttribute('data-nav-card');
    if (section && card) {
      e.preventDefault();
      expandSectionAndScroll(section, card);
      document.querySelectorAll('.app-bottom-nav__btn').forEach((btn) => {
        btn.classList.toggle('is-active', btn.getAttribute('data-nav-card') === card);
      });
    }
  });
}
