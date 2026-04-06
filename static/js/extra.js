/* ═══════════════════════════════════════════════════════
   TASKSPHERE — dashboard-extras.js
   Extra chart helpers, animated counters, sparklines
═══════════════════════════════════════════════════════ */

/* ── SPARKLINE MINI CHARTS ──────────────────────────── */
function renderSparkline(canvasId, data, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  new Chart(canvas, {
    type: 'line',
    data: {
      labels: data.map((_, i) => i),
      datasets: [{
        data,
        borderColor:     color,
        backgroundColor: color + '22',
        borderWidth:     2,
        fill:            true,
        tension:         0.4,
        pointRadius:     0,
      }]
    },
    options: {
      responsive: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales:  { x: { display: false }, y: { display: false } },
      animation: { duration: 800, easing: 'easeInOutQuart' },
    }
  });
}

/* ── RADIAL PROGRESS ────────────────────────────────── */
function renderRadial(canvasId, value, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [value, 100 - value],
        backgroundColor: [color, 'rgba(99,130,255,.08)'],
        borderWidth: 0,
        hoverOffset: 0,
      }]
    },
    options: {
      cutout:    '80%',
      responsive: false,
      plugins: {
        legend:  { display: false },
        tooltip: { enabled: false },
      },
      animation: { animateRotate: true, duration: 900 }
    }
  });
}

/* ── HORIZONTAL BAR (team workload) ─────────────────── */
function renderHorizontalBar(canvasId, labels, data, colors) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || labels.map((_, i) => `hsl(${i * 45 + 200},70%,60%)`),
        borderRadius:     6,
        borderSkipped:    false,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {
        legend:  { display: false },
        tooltip: {
          backgroundColor: '#121929',
          borderColor:     '#2d3654',
          borderWidth:     1,
        }
      },
      scales: {
        x: { grid: { color: 'rgba(99,130,255,.07)' }, ticks: { color: '#9da8c9', font: { size: 11 } } },
        y: { grid: { display: false },                ticks: { color: '#9da8c9', font: { size: 11 } } },
      }
    }
  });
}

/* ── STACKED BAR CHART ───────────────────────────────── */
function renderStackedBar(canvasId, labels, datasets) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#9da8c9', font: { size: 11 }, boxWidth: 12 } },
        tooltip: { backgroundColor: '#121929', borderColor: '#2d3654', borderWidth: 1 }
      },
      scales: {
        x: { stacked: true, grid: { color: 'rgba(99,130,255,.07)' }, ticks: { color: '#9da8c9' } },
        y: { stacked: true, grid: { color: 'rgba(99,130,255,.07)' }, ticks: { color: '#9da8c9' } },
      }
    }
  });
}

/* ── ANIMATED NUMBER TICKER ──────────────────────────── */
function ticker(el, from, to, duration = 1200, suffix = '') {
  if (!el) return;
  const startTime = performance.now();
  function step(currentTime) {
    const elapsed  = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease     = 1 - Math.pow(1 - progress, 4); // easeOutQuart
    const value    = Math.round(from + (to - from) * ease);
    el.textContent = value.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
window.ticker = ticker;

/* ── TYPEWRITER EFFECT ───────────────────────────────── */
function typewriter(el, text, speed = 60) {
  if (!el) return;
  el.textContent = '';
  let i = 0;
  const iv = setInterval(() => {
    el.textContent += text[i++];
    if (i >= text.length) clearInterval(iv);
  }, speed);
}
window.typewriter = typewriter;

/* ── CONFETTI BURST (for task completion) ───────────── */
function confettiBurst() {
  const colors = ['#6366f1','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899'];
  const container = document.body;
  for (let i = 0; i < 60; i++) {
    const el = document.createElement('div');
    el.style.cssText = `
      position:fixed; z-index:9999; pointer-events:none;
      width:${Math.random()*8+4}px; height:${Math.random()*8+4}px;
      background:${colors[Math.floor(Math.random()*colors.length)]};
      border-radius:${Math.random()>.5?'50%':'2px'};
      left:${Math.random()*100}vw; top:-10px;
      animation: confettiFall ${Math.random()*2+1.5}s ease-in forwards;
      transform: rotate(${Math.random()*360}deg);
    `;
    container.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }
}
window.confettiBurst = confettiBurst;

// Inject confetti keyframes
if (!document.getElementById('confettiStyle')) {
  const s = document.createElement('style');
  s.id = 'confettiStyle';
  s.textContent = `
    @keyframes confettiFall {
      to {
        transform: translateY(110vh) rotate(${Math.random()*720}deg);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(s);
}

/* ── REAL-TIME CLOCK ─────────────────────────────────── */
function startClock(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  function update() {
    el.textContent = new Date().toLocaleTimeString('en-US', {
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
  }
  update();
  setInterval(update, 1000);
}
window.startClock = startClock;

/* ── SCROLL-TO-TOP BUTTON ────────────────────────────── */
(function() {
  const btn = document.createElement('button');
  btn.id = 'scrollTopBtn';
  btn.innerHTML = '<i class="fas fa-chevron-up"></i>';
  btn.style.cssText = `
    position:fixed; bottom:80px; right:24px; z-index:400;
    width:38px; height:38px; border-radius:50%;
    background:var(--accent); color:#fff; border:none; cursor:pointer;
    display:none; align-items:center; justify-content:center;
    font-size:.85rem; box-shadow:0 4px 16px var(--accent-glow);
    transition:all .25s; opacity:.85;
  `;
  btn.addEventListener('click', () => {
    document.getElementById('pageContent')?.scrollTo({ top: 0, behavior: 'smooth' });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  btn.addEventListener('mouseenter', () => btn.style.opacity = '1');
  btn.addEventListener('mouseleave', () => btn.style.opacity = '.85');
  document.addEventListener('DOMContentLoaded', () => document.body.appendChild(btn));

  const pageContent = () => document.getElementById('pageContent') || window;
  function checkScroll() {
    const pc = document.getElementById('pageContent');
    const scrollY = pc ? pc.scrollTop : window.scrollY;
    btn.style.display = scrollY > 300 ? 'flex' : 'none';
  }
  document.addEventListener('scroll', checkScroll, true);
  window.addEventListener('scroll', checkScroll);
})();

/* ── KEYBOARD SHORTCUTS ──────────────────────────────── */
document.addEventListener('keydown', e => {
  // Ctrl+K — focus search
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    document.getElementById('globalSearch')?.focus();
  }
  // Escape — close modal
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.show').forEach(m => {
      m.classList.remove('show');
      document.body.style.overflow = '';
    });
    document.getElementById('searchResults')?.classList.remove('show');
    document.getElementById('notifDropdown')?.classList.remove('show');
  }
  // Ctrl+N — new task (on tasks page)
  if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
    e.preventDefault();
    if (window.openNewTaskModal) window.openNewTaskModal();
  }
});

/* ── RIPPLE EFFECT ON BUTTONS ────────────────────────── */
document.addEventListener('click', function(e) {
  const btn = e.target.closest('.btn');
  if (!btn) return;
  const ripple = document.createElement('span');
  const rect   = btn.getBoundingClientRect();
  const size   = Math.max(rect.width, rect.height);
  ripple.style.cssText = `
    position:absolute; border-radius:50%;
    width:${size}px; height:${size}px;
    left:${e.clientX - rect.left - size/2}px;
    top:${e.clientY - rect.top  - size/2}px;
    background:rgba(255,255,255,.25);
    transform:scale(0); animation:rippleAnim .5s ease forwards;
    pointer-events:none;
  `;
  btn.style.position = 'relative';
  btn.style.overflow = 'hidden';
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
});

if (!document.getElementById('rippleStyle')) {
  const s = document.createElement('style');
  s.id = 'rippleStyle';
  s.textContent = '@keyframes rippleAnim { to { transform:scale(2.5); opacity:0; } }';
  document.head.appendChild(s);
}

/* ── LAZY LOAD IMAGES ────────────────────────────────── */
function lazyLoadImages() {
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          const img = e.target;
          if (img.dataset.src) { img.src = img.dataset.src; delete img.dataset.src; }
          observer.unobserve(img);
        }
      });
    }, { rootMargin: '50px' });
    document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
  }
}
document.addEventListener('DOMContentLoaded', lazyLoadImages);

/* ── TOOLTIP HELPER ──────────────────────────────────── */
function initTooltips() {
  document.querySelectorAll('[title]').forEach(el => {
    el.setAttribute('data-tooltip', el.getAttribute('title'));
    el.removeAttribute('title');
    el.addEventListener('mouseenter', showTooltip);
    el.addEventListener('mouseleave', hideTooltip);
  });
}

function showTooltip(e) {
  const text = e.currentTarget.dataset.tooltip;
  if (!text) return;
  const tip = document.createElement('div');
  tip.id = 'ts-tooltip';
  tip.textContent = text;
  tip.style.cssText = `
    position:fixed; z-index:9000;
    background:var(--bg-card); border:1px solid var(--border);
    color:var(--text-primary); font-size:.75rem; font-weight:500;
    padding:5px 10px; border-radius:7px;
    pointer-events:none; white-space:nowrap;
    box-shadow:0 4px 16px rgba(0,0,0,.3);
    animation:tooltipFade .15s ease;
  `;
  document.body.appendChild(tip);
  const rect = e.currentTarget.getBoundingClientRect();
  tip.style.left = rect.left + rect.width / 2 - tip.offsetWidth / 2 + 'px';
  tip.style.top  = rect.top  - tip.offsetHeight - 8 + 'px';
}
function hideTooltip() { document.getElementById('ts-tooltip')?.remove(); }

if (!document.getElementById('tooltipStyle')) {
  const s = document.createElement('style');
  s.id = 'tooltipStyle';
  s.textContent = '@keyframes tooltipFade { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }';
  document.head.appendChild(s);
}
document.addEventListener('DOMContentLoaded', initTooltips);