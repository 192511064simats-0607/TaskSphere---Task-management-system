/* ═══════════════════════════════════════════
   TASKSPHERE — APP.JS  (Core client logic)
═══════════════════════════════════════════ */

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
  AOS.init({ duration: 560, once: true, offset: 30, easing: 'ease-out-cubic' });
  initLoader();
  initSidebar();
  initDarkMode();
  initSearch();
  initNotifications();
  initSocket();
  initTopbarActions();
});

// ── LOADER ──
function initLoader() {
  window.addEventListener('load', () => {
    setTimeout(() => {
      document.getElementById('loader')?.classList.add('hidden');
    }, 800);
  });
  // fallback
  setTimeout(() => document.getElementById('loader')?.classList.add('hidden'), 2500);
}

// ── SIDEBAR ──
function initSidebar() {
  const sidebar   = document.getElementById('sidebar');
  const mainWrap  = document.getElementById('mainWrap');
  const toggle    = document.getElementById('sidebarToggle');
  const mobileBtn = document.getElementById('mobileMenuBtn');

  const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (collapsed) { sidebar?.classList.add('collapsed'); mainWrap?.classList.add('expanded'); }

  toggle?.addEventListener('click', () => {
    const isCollapsed = sidebar.classList.toggle('collapsed');
    mainWrap?.classList.toggle('expanded', isCollapsed);
    localStorage.setItem('sidebarCollapsed', isCollapsed);
  });

  mobileBtn?.addEventListener('click', () => sidebar?.classList.toggle('open'));

  document.addEventListener('click', e => {
    if (window.innerWidth < 900 && sidebar?.classList.contains('open')) {
      if (!sidebar.contains(e.target) && e.target !== mobileBtn) {
        sidebar.classList.remove('open');
      }
    }
  });
}

// ── DARK MODE ──
function initDarkMode() {
  const btn  = document.getElementById('darkModeBtn');
  const icon = document.getElementById('darkModeIcon');
  const theme = localStorage.getItem('theme') || 'dark';
  applyTheme(theme);

  btn?.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next    = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('theme', next);
  });
}
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('darkModeIcon');
  if (icon) { icon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun'; }
}

// ── SEARCH ──
function initSearch() {
  const input   = document.getElementById('globalSearch');
  const results = document.getElementById('searchResults');
  let debounce;

  input?.addEventListener('input', () => {
    clearTimeout(debounce);
    const q = input.value.trim();
    if (!q) { results.classList.remove('show'); return; }
    debounce = setTimeout(() => performSearch(q), 300);
  });

  input?.addEventListener('focus', () => {
    if (input.value.trim()) results.classList.add('show');
  });

  document.addEventListener('click', e => {
    if (!input?.contains(e.target) && !results?.contains(e.target)) {
      results?.classList.remove('show');
    }
  });
}

async function performSearch(q) {
  try {
    const res  = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderSearchResults(data);
  } catch {}
}

function renderSearchResults({ tasks = [], projects = [] }) {
  const results = document.getElementById('searchResults');
  if (!results) return;
  const all = [...projects.map(p => ({ ...p, _type: 'project' })), ...tasks.map(t => ({ ...t, _type: 'task' }))];
  if (!all.length) {
    results.innerHTML = `<div class="search-result-item"><i class="fas fa-search"></i> No results found</div>`;
  } else {
    results.innerHTML = all.map(item => `
      <div class="search-result-item" onclick="navigateTo('${item._type}', '${item._id}')">
        <i class="fas fa-${item._type === 'project' ? 'folder' : 'check-square'}"></i>
        <span>${item.name || item.title}</span>
        <span class="text-muted text-sm" style="margin-left:auto">${item._type}</span>
      </div>
    `).join('');
  }
  results.classList.add('show');
}

function navigateTo(type, id) {
  if (type === 'project') window.location.href = `/projects?highlight=${id}`;
  else window.location.href = `/tasks?highlight=${id}`;
  document.getElementById('searchResults')?.classList.remove('show');
  document.getElementById('globalSearch').value = '';
}

// ── NOTIFICATIONS ──
function initNotifications() {
  loadNotifications();
  const btn  = document.getElementById('notifBtn');
  const drop = document.getElementById('notifDropdown');

  btn?.addEventListener('click', e => {
    e.stopPropagation();
    drop?.classList.toggle('show');
  });
  document.addEventListener('click', e => {
    if (!drop?.contains(e.target) && e.target !== btn) drop?.classList.remove('show');
  });
}

async function loadNotifications() {
  try {
    const res  = await fetch('/api/notifications');
    const data = await res.json();
    renderNotifications(data);
  } catch {}
}

function renderNotifications(notifs) {
  const list  = document.getElementById('notifList');
  const badge = document.getElementById('notifBadge');
  if (!list) return;

  const unread = notifs.filter(n => !n.read).length;
  if (badge) { badge.textContent = unread; badge.style.display = unread ? 'flex' : 'none'; }

  if (!notifs.length) {
    list.innerHTML = `<div class="notif-empty"><i class="fas fa-check-circle"></i> All caught up!</div>`;
    return;
  }
  list.innerHTML = notifs.map(n => `
    <div class="notif-item ${n.read ? '' : 'unread'}">
      <div class="notif-icon ${n.type || 'info'}">
        <i class="fas fa-${n.type === 'task' ? 'list-check' : n.type === 'success' ? 'check' : 'bell'}"></i>
      </div>
      <div class="notif-text">
        <strong>${esc(n.title)}</strong>
        ${esc(n.message)}
        <small>${formatTime(n.timestamp)}</small>
      </div>
    </div>
  `).join('');
}

async function markAllRead() {
  await fetch('/api/notifications/read', { method: 'POST' });
  loadNotifications();
}
window.markAllRead = markAllRead;

// ── SOCKET.IO ──
let socket;
function initSocket() {
  try {
    socket = io({ transports: ['websocket', 'polling'] });
    socket.on('connect',       ()  => console.log('🔌 Socket connected'));
    socket.on('notification',  n   => {
      showToast('info', n.title, n.message);
      loadNotifications();
    });
    socket.on('task_created',  d   => onTaskEvent('created', d));
    socket.on('task_updated',  d   => onTaskEvent('updated', d));
    socket.on('task_deleted',  d   => onTaskEvent('deleted', d));
    socket.on('task_completed',d   => showToast('success', '✅ Task Completed', d.title));
    socket.on('kanban_move',   d   => { if (window.refreshKanban) window.refreshKanban(); });
    socket.on('project_created',d  => { if (window.loadProjects) window.loadProjects(); });
    socket.on('new_comment',   d   => { if (window.handleNewComment) window.handleNewComment(d); });
  } catch(e) { console.warn('Socket unavailable', e); }
}

function onTaskEvent(type, data) {
  if (window.loadTasks)   window.loadTasks();
  if (window.refreshKanban) window.refreshKanban();
}

// ── TOPBAR ──
function initTopbarActions() {
  document.getElementById('topbarAvatarBtn')?.addEventListener('click', () => {
    window.location.href = '/profile';
  });
}

// ── TOAST ──
function showToast(type, title, message) {
  const icons = { success: 'check-circle', error: 'xmark-circle', info: 'info-circle' };
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-icon"><i class="fas fa-${icons[type] || 'bell'}"></i></div>
    <div class="toast-body"><strong>${esc(title)}</strong><span>${esc(message || '')}</span></div>
    <button class="toast-close" onclick="removeToast(this.parentElement)"><i class="fas fa-xmark"></i></button>
  `;
  container.appendChild(toast);
  setTimeout(() => removeToast(toast), 4500);
}
window.showToast = showToast;

function removeToast(el) {
  el?.classList.add('removing');
  setTimeout(() => el?.remove(), 350);
}
window.removeToast = removeToast;

// ── MODAL HELPERS ──
function openModal(id) {
  document.getElementById(id)?.classList.add('show');
  document.body.style.overflow = 'hidden';
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('show');
  document.body.style.overflow = '';
}
window.openModal  = openModal;
window.closeModal = closeModal;

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('show');
    document.body.style.overflow = '';
  }
  if (e.target.classList.contains('modal-close')) {
    e.target.closest('.modal-backdrop')?.classList.remove('show');
    document.body.style.overflow = '';
  }
});

// ── API HELPERS ──
async function apiGet(url)       { const r = await fetch(url); return r.json(); }
async function apiPost(url, body){ const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) }); return r.json(); }
async function apiPut(url, body) { const r = await fetch(url, { method:'PUT',  headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) }); return r.json(); }
async function apiDelete(url)    { const r = await fetch(url, { method:'DELETE' }); return r.json(); }
window.apiGet    = apiGet;
window.apiPost   = apiPost;
window.apiPut    = apiPut;
window.apiDelete = apiDelete;

// ── FORMAT HELPERS ──
function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts), now = Date.now();
  const diff = now - d.getTime();
  if (diff < 60000)   return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff/60000)}m ago`;
  if (diff < 86400000)return `${Math.floor(diff/3600000)}h ago`;
  return d.toLocaleDateString('en-US', { month:'short', day:'numeric' });
}
function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function priorityBadge(p) { return `<span class="badge-pill badge-${p}">${p}</span>`; }
function statusBadge(s)   { return `<span class="badge-pill badge-${s}">${s.replace('_',' ')}</span>`; }
function deadlineClass(d) {
  if (!d) return '';
  const diff = new Date(d) - Date.now();
  if (diff < 0) return 'text-danger';
  if (diff < 86400000 * 2) return 'text-warning';
  return '';
}
window.formatTime    = formatTime;
window.esc           = esc;
window.priorityBadge = priorityBadge;
window.statusBadge   = statusBadge;
window.deadlineClass = deadlineClass;

// ── CONFIRM DIALOG ──
function confirmAction(msg, cb) {
  if (confirm(msg)) cb();
}
window.confirmAction = confirmAction;

// ── SCROLL ANIMATE ──
function animateCount(el, target, duration = 1000) {
  if (!el) return;
  let start = 0, step = target / (duration / 16);
  const tick = () => {
    start = Math.min(start + step, target);
    el.textContent = Math.round(start);
    if (start < target) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
window.animateCount = animateCount;