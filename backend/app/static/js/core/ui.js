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
  setTimeout(() => {
    toast.className = 'toast hidden';
  }, 2500);
}
