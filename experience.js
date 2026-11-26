/* Experience and open calls (Spain page and the log page es/bitacora.html). Static content only: no requests, no personal data.
   - [data-open-call data-closes="YYYY-MM-DD"]: the last day is included (the visitor's own date). Until then a
     [data-open-call-countdown] says how many days are left; after it the card gets .is-closed and every element with
     data-closed-text / data-closed-href inside it swaps its text / link.
   - [data-prefill-places], or ?lugar=… in the address: carries the trip into the first-contact form («Lugar o lugares pertinentes»).
   - [data-pedigree]: the before/after tree. Shown as «after» without JavaScript; if it is below the fold it starts
     as «before» and plays once when it comes into view (not with reduced motion). */
(() => {
  const es = document.documentElement.lang === 'es';
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const T = es ? {
    today: 'Hoy es el último día para enviarla.',
    tomorrow: 'Mañana es el último día. Hay pocas plazas.',
    left: n => `Quedan ${n} días. Hay pocas plazas.`
  } : {
    today: 'Today is the last day to send it.',
    tomorrow: 'Tomorrow is the last day. Places are limited.',
    left: n => `${n} days left. Places are limited.`
  };

  // Open calls: countdown, then «closed» on its own once the date has passed.
  const now = new Date();
  const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  document.querySelectorAll('[data-open-call]').forEach(call => {
    const [y, m, d] = (call.dataset.closes || '').split('-').map(Number);
    if (!y || !m || !d) return;
    const left = Math.round((Date.UTC(y, m - 1, d) - today) / 86400000);
    if (left < 0) {
      call.classList.add('is-closed');
      call.querySelectorAll('[data-closed-text]').forEach(el => { el.textContent = el.dataset.closedText; });
      call.querySelectorAll('[data-closed-href]').forEach(el => {
        el.setAttribute('href', el.dataset.closedHref);
        el.removeAttribute('data-prefill-places');
      });
      return;
    }
    const countdown = call.querySelector('[data-open-call-countdown]');
    if (countdown) countdown.textContent = left === 0 ? T.today : left === 1 ? T.tomorrow : T.left(left);
  });

  // «Book my search»: the trip goes into the places field, without erasing what the visitor already wrote.
  // From another page (the log) the place comes as ?lugar=… in the link to spain.html#contact.
  const placesField = document.querySelector('#inquiry-places');
  const plain = text => text.toLocaleLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
  const prefill = place => {
    if (!placesField || !place) return;
    const current = placesField.value.trim();
    if (!current) placesField.value = place.slice(0, 180);
    else if (!plain(current).includes(plain(place))) placesField.value = `${place}; ${current}`.slice(0, 180);
  };
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-prefill-places]');
    if (link) prefill(link.dataset.prefillPlaces);
  });
  prefill((new URLSearchParams(window.location.search).get('lugar') || '').trim());

  // Before/after tree.
  document.querySelectorAll('[data-pedigree]').forEach(fig => {
    const buttons = [...fig.querySelectorAll('[data-pedigree-show]')];
    let timer = 0;
    const show = (state, animate) => {
      fig.dataset.state = state;
      buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.pedigreeShow === state)));
      fig.classList.remove('is-playing');
      if (animate && state === 'after' && !reduceMotion) {
        void fig.offsetWidth;            // restart the arrival animation
        fig.classList.add('is-playing');
      }
    };
    buttons.forEach(button => button.addEventListener('click', () => {
      clearTimeout(timer);
      show(button.dataset.pedigreeShow, true);
    }));
    if (reduceMotion || !('IntersectionObserver' in window)) return;
    if (fig.getBoundingClientRect().top < window.innerHeight) return;   // already on screen: keep the result
    show('before', false);
    const observer = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      observer.disconnect();
      timer = setTimeout(() => show('after', true), 1400);
    }, { threshold: 0.45 });
    observer.observe(fig);
  });
})();
