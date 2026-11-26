/* Floating notice for open requests, on every page (EN and ES).
   To announce a new trip, add an entry to AVISOS: it is the only place to edit for the whole site. A notice shows
   from the page load until its last day (`closes`, included, the visitor's own date). A visitor can close it; that is
   remembered in this browser only. On the page that holds the poster it hides while the poster is on screen.
   Static content only: no requests, no personal data. */
(() => {
  const AVISOS = [
    {
      id: 'canarias-2026-11',
      closes: '2026-11-30',
      image: 'images/scenes/canarias-solicitudes.jpg',
      es: {
        badge: 'Solicitudes abiertas',
        title: 'Viaje a Canarias',
        text: 'Archivos diocesanos de La Laguna (Tenerife) y Las Palmas (Gran Canaria).',
        action: 'Ver el cartel y reservar',
        href: 'es/spain.html#open-calls'
      },
      en: {
        badge: 'Requests open',
        title: 'Trip to the Canary Islands',
        text: 'Diocesan archives of La Laguna (Tenerife) and Las Palmas (Gran Canaria).',
        action: 'See the poster and book',
        href: 'spain.html#open-calls'
      }
    }
  ];

  const script = document.currentScript;
  if (!script) return;
  const root = new URL('.', script.src);
  const lang = document.documentElement.lang === 'es' ? 'es' : 'en';
  const T = lang === 'es' ? {
    region: 'Aviso: solicitudes abiertas', close: 'Cerrar aviso', all: 'Todos los viajes',
    today: 'último día', tomorrow: 'hasta mañana', left: n => `quedan ${n} días`
  } : {
    region: 'Notice: open requests', close: 'Close notice', all: 'All trips',
    today: 'last day', tomorrow: 'until tomorrow', left: n => `${n} days left`
  };
  const storage = {
    get: key => { try { return window.localStorage.getItem(key); } catch (error) { return null; } },
    set: (key, value) => { try { window.localStorage.setItem(key, value); } catch (error) { /* private mode */ } }
  };
  const now = new Date();
  const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const daysLeft = closes => {
    const [y, m, d] = closes.split('-').map(Number);
    return Math.round((Date.UTC(y, m - 1, d) - today) / 86400000);
  };
  const open = AVISOS
    .map(aviso => ({ ...aviso, left: daysLeft(aviso.closes) }))
    .filter(aviso => aviso.left >= 0 && !storage.get(`magenha-aviso:${aviso.id}`))
    .sort((a, b) => a.left - b.left);
  if (!open.length) return;
  const aviso = open[0];
  const text = aviso[lang];

  const el = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    node.append(...children);
    return node;
  };
  const href = new URL(text.href, root);
  const when = aviso.left === 0 ? T.today : aviso.left === 1 ? T.tomorrow : T.left(aviso.left);
  const close = el('button', { type: 'button', class: 'notice__close', 'aria-label': T.close }, '×');
  const notice = el('aside', { class: 'notice', 'aria-label': T.region },
    el('a', { class: 'notice__image', href: href.href, tabindex: '-1', 'aria-hidden': 'true' },
      el('img', { src: new URL(aviso.image, root).href, alt: '', width: '72', height: '90', loading: 'lazy', decoding: 'async' })),
    el('div', { class: 'notice__body' },
      el('p', { class: 'notice__badge' }, el('span', { class: 'notice__dot', 'aria-hidden': 'true' }), `${text.badge} · ${when}`),
      el('p', { class: 'notice__title' }, text.title),
      el('p', { class: 'notice__text' }, text.text),
      el('p', { class: 'notice__actions' },
        el('a', { class: 'notice__action', href: href.href }, `${text.action} `, el('span', { 'aria-hidden': 'true' }, '→')),
        el('a', { class: 'notice__more', href: new URL(lang === 'es' ? 'es/log.html#proximos' : 'log.html#proximos', root).href }, T.all))),
    close);

  const hide = remember => {
    notice.classList.remove('is-visible');
    if (remember) {
      storage.set(`magenha-aviso:${aviso.id}`, 'cerrado');
      window.setTimeout(() => notice.remove(), 400);
    }
  };
  close.addEventListener('click', () => hide(true));
  notice.addEventListener('keydown', event => { if (event.key === 'Escape') hide(true); });

  // On the page with the poster itself, step aside while the poster is on screen.
  const samePage = href.pathname === window.location.pathname && href.hash && document.querySelector(href.hash);
  let targetVisible = false;
  const update = () => notice.classList.toggle('is-covered', targetVisible);
  if (samePage && 'IntersectionObserver' in window) {
    new IntersectionObserver(entries => { targetVisible = entries.some(entry => entry.isIntersecting); update(); },
      { threshold: 0.15 }).observe(document.querySelector(href.hash));
  }

  document.body.append(notice);
  window.setTimeout(() => notice.classList.add('is-visible'), 1400);
})();
