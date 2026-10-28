/* Public coverage search and map: localities, area names, scope and outlines only. No archive records or personal data. */
(() => {
  const section = document.getElementById('coverage');
  if (!section) return;
  const es = document.documentElement.lang === 'es';
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const NS = 'http://www.w3.org/2000/svg';
  const T = es ? {
    badge: { available: 'VIABLE', limited: 'CON CONDICIONES', unavailable: 'NO VIABLE', unknown: 'SIN DATOS', mixed: 'DEPENDE' },
    group: { available: 'Viable', limited: 'Viable con condiciones', unavailable: 'No viable por ahora' },
    hint: 'Escriba al menos dos letras de su localidad o provincia.',
    loading: 'Consultando…',
    error: 'No se pudo consultar la cobertura. Esto no indica falta de cobertura: solicite la evaluación por correo o vuelva a intentarlo.',
    availableLocality: l => `¡Buenas noticias! Podemos investigar en ${l}`,
    unavailableLocality: l => `Por ahora no podemos investigar en ${l}`,
    severalProvinces: q => `«${q}» aparece en varias provincias`,
    availableProvince: p => `Investigamos en la provincia de ${p}`,
    unavailableProvince: p => `Por ahora no investigamos en la provincia de ${p}`,
    mixedProvince: p => `En la provincia de ${p}, depende de la localidad`,
    unknown: q => `No encontramos «${q}» en nuestros datos`,
    noteAvailable: 'Viable no garantiza que los libros se conserven ni una cita inmediata: lo confirmamos en la evaluación individual, que es gratuita.',
    noteUnavailable: 'Hoy no tenemos una vía estable para consultar los archivos de esta diócesis. Escríbanos igualmente: le avisaremos si cambia.',
    noteSeveral: 'Elija la suya en la lista de abajo.',
    noteProvince: 'Busque su localidad exacta para confirmarlo.',
    noteUnknown: 'Muchas localidades pequeñas no figuran en la lista; eso no significa que no podamos ayudarle. Pida una evaluación individual y lo comprobamos.',
    viable: n => `${n} ${n === 1 ? 'viable' : 'viables'}`,
    notViable: n => `${n} no ${n === 1 ? 'viable' : 'viables'}`,
    matches: (n, q) => `${n} ${n === 1 ? 'localidad coincide' : 'localidades coinciden'} con «${q}»`,
    assess: 'Solicitar evaluación gratuita',
    writeAnyway: 'Escribirnos igualmente',
    seeMap: 'Ver en el mapa',
    more: n => `Mostrar más (${n})`,
    showOnMap: 'Ver su diócesis en el mapa',
    infoPrompt: 'Señale o toque una diócesis para ver si es viable.',
    info: { available: 'Investigamos en esta diócesis.', limited: 'Investigamos en esta diócesis, con condiciones.',
            unavailable: 'Por ahora no investigamos en esta diócesis.' },
    dioceses: n => `${n} diócesis`,
    of: 'de', municipalities: 'municipios',
    mapError: 'No se pudo cargar el mapa. Use el buscador o solicite una evaluación por correo.'
  } : {
    badge: { available: 'VIABLE', limited: 'WITH CONDITIONS', unavailable: 'NOT VIABLE', unknown: 'NOT IN OUR DATA', mixed: 'IT DEPENDS' },
    group: { available: 'Viable', limited: 'Viable with conditions', unavailable: 'Not viable for now' },
    hint: 'Type at least two letters of your locality or province.',
    loading: 'Checking…',
    error: 'Coverage could not be loaded. This does not indicate a lack of coverage: request an assessment by email or try again.',
    availableLocality: l => `Good news! We can research in ${l}`,
    unavailableLocality: l => `For now we cannot research in ${l}`,
    severalProvinces: q => `“${q}” appears in several provinces`,
    availableProvince: p => `We research in the province of ${p}`,
    unavailableProvince: p => `For now we do not research in the province of ${p}`,
    mixedProvince: p => `In the province of ${p}, it depends on the locality`,
    unknown: q => `We could not find “${q}” in our data`,
    noteAvailable: 'Viable does not guarantee that the records survive or an immediate appointment: we confirm it in the individual assessment, which is free.',
    noteUnavailable: 'We do not currently have a stable route to the archives of this diocese. Write to us anyway: we will let you know if this changes.',
    noteSeveral: 'Choose yours in the list below.',
    noteProvince: 'Search for your exact locality to confirm it.',
    noteUnknown: 'Many small places are not on the list; that does not mean we cannot help. Request an individual assessment and we will check.',
    viable: n => `${n} viable`,
    notViable: n => `${n} not viable`,
    matches: (n, q) => `${n} ${n === 1 ? 'locality matches' : 'localities match'} “${q}”`,
    assess: 'Request a free assessment',
    writeAnyway: 'Write to us anyway',
    seeMap: 'See it on the map',
    more: n => `Show more (${n})`,
    showOnMap: 'Show its diocese on the map',
    infoPrompt: 'Point at or tap a diocese to see whether it is viable.',
    info: { available: 'We research in this diocese.', limited: 'We research in this diocese, with conditions.',
            unavailable: 'For now we do not research in this diocese.' },
    dioceses: n => `${n} ${n === 1 ? 'diocese' : 'dioceses'}`,
    of: 'of', municipalities: 'municipalities',
    mapError: 'The map could not be loaded. Use the search or request an assessment by email.'
  };
  const STATUSES = ['available', 'limited', 'unavailable'];
  const normalise = value => value.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase().trim();

  const h = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === 'class') node.className = v;
      else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? '' : v);
    }
    node.append(...children.filter(c => c != null && c !== false));
    return node;
  };
  const s = (name, attrs = {}) => {
    const node = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    return node;
  };
  const MOUTH = { available: 'M14 28 Q24 39 34 28', limited: 'M15 31 H33', unavailable: 'M15 36 Q24 27 33 36',
                  unknown: 'M15 32 Q19.5 28.5 24 32 T33 31', mixed: 'M15 31 H33' };
  const face = (kind, size) => {
    const svg = s('svg', { viewBox: '0 0 48 48', width: size, height: size, 'aria-hidden': 'true', class: `coverage-face coverage-face--${kind}` });
    svg.append(s('circle', { cx: 24, cy: 24, r: 21, class: 'coverage-face__head' }),
      s('circle', { cx: 16.5, cy: 19.5, r: 2.8, class: 'coverage-face__eye' }),
      s('circle', { cx: 31.5, cy: 19.5, r: 2.8, class: 'coverage-face__eye' }),
      s('path', { d: MOUTH[kind], class: 'coverage-face__mouth' }));
    if (kind === 'unavailable') svg.append(s('path', { d: 'M33.5 24 q2.6 4.2 0 6.4 q-2.6 -2.2 0 -6.4z', class: 'coverage-face__tear' }));
    return svg;
  };
  const badge = kind => h('span', { class: `coverage-badge coverage-badge--${kind}` }, T.badge[kind]);
  const scrollTo = node => node.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });

  /* The map: every diocese, green where we research, hatched red where we do not for now. */
  const map = (() => {
    const figure = section.querySelector('[data-coverage-map]');
    if (!figure) return { select() {} };
    const canvas = figure.querySelector('[data-coverage-map-canvas]');
    const legend = figure.querySelector('[data-coverage-legend]');
    const info = figure.querySelector('[data-coverage-info]');
    const list = figure.querySelector('[data-coverage-areas]');
    // Plain equirectangular grid; the Canary Islands move to an inset south-west of the peninsula.
    const K = Math.cos(40 * Math.PI / 180);
    const proj = ([lon, lat]) => {
      if (lon < -13 && lat < 30) { lon += 6.2; lat += 7; }
      return `${((lon + 12.5) * K * 60).toFixed(1)},${((44.2 - lat) * 60).toFixed(1)}`;
    };
    const W = Math.ceil(17.1 * K * 60), H = Math.ceil(9.8 * 60);
    const scope = area => area.scope.map(p => p.whole ? p.province
      : p.places.length ? `${p.province}: ${p.places.join(', ')}`
        : `${p.province} (${p.municipalities} ${T.of} ${p.total} ${T.municipalities})`).join('; ');
    const areas = new Map();
    let svg, tip, borders, active = null, pending = null;

    const renderInfo = area => {
      info.className = `coverage-map__info${area ? ` is-${area.status}` : ''}`;
      if (!area) {
        const counts = STATUSES.map(st => [st, [...areas.values()].filter(a => a.status === st).length]).filter(([, n]) => n);
        info.replaceChildren(h('div', { class: 'coverage-map__info-head' }, face('unknown', 40),
          h('p', {}, T.infoPrompt, h('br'), h('small', {}, counts.map(([st, n]) => `${T.group[st]}: ${T.dioceses(n)}`).join(' · ')))));
        return;
      }
      const action = area.status === 'unavailable' ? T.writeAnyway : T.assess;
      info.replaceChildren(
        h('div', { class: 'coverage-map__info-head' }, face(area.status, 48),
          h('div', {}, badge(area.status), h('h3', {}, area.name))),
        h('p', {}, h('strong', {}, T.info[area.status]), ' ', scope(area)),
        h('a', { class: 'text-link', href: '#contact' }, `${action} →`));
    };
    const activate = area => {
      active = area;
      for (const a of areas.values()) {
        a.path.classList.toggle('is-active', a === area);
        a.button.classList.toggle('is-active', a === area);
      }
      svg.classList.toggle('has-active', Boolean(area));
      if (area) svg.insertBefore(area.path, borders);
      renderInfo(area);
    };
    const showTip = (area, event) => {
      const box = canvas.getBoundingClientRect();
      tip.replaceChildren(h('strong', {}, area.name), ' ', badge(area.status));
      tip.style.left = `${event.clientX - box.left}px`;
      tip.style.top = `${event.clientY - box.top}px`;
      tip.hidden = false;
    };

    // The coverage changes with each export: always ask the server whether the file is still current.
    fetch(figure.dataset.url, { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error('Map unavailable'); return r.json(); }).then(data => {
      if (!Array.isArray(data.areas) || !Array.isArray(data.borders)) throw new Error('Invalid map');
      svg = s('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': figure.getAttribute('aria-label') });
      const defs = s('defs');
      const hatch = s('pattern', { id: 'coverage-hatch', patternUnits: 'userSpaceOnUse', width: 7, height: 7, patternTransform: 'rotate(45)' });
      hatch.append(s('rect', { width: 7, height: 7, class: 'coverage-hatch__base' }), s('rect', { width: 2.4, height: 7, class: 'coverage-hatch__line' }));
      defs.append(hatch);
      svg.append(defs);
      const a = proj([-18.4, 29.5]).split(','), b = proj([-13.2, 27.5]).split(',');
      svg.append(s('rect', { class: 'coverage-map__inset', x: a[0], y: a[1], width: b[0] - a[0], height: b[1] - a[1] }));
      const groups = Object.fromEntries(STATUSES.map(st => [st, []]));
      // An area with a status this page does not know is left out: only a known status may be painted.
      data.areas.filter(area => STATUSES.includes(area.status)).forEach((area, i) => {
        const status = area.status;
        const d = area.polygons.map(poly => poly.map(ring => 'M' + ring.map(proj).join('L') + 'Z').join('')).join('');
        const path = s('path', { d, class: `coverage-map__area is-${status}`, style: `--i:${i}` });
        const entry = { ...area, status, path };
        path.addEventListener('pointermove', event => { if (event.pointerType !== 'touch') showTip(entry, event); });
        path.addEventListener('pointerenter', () => path.classList.add('is-hover'));
        path.addEventListener('pointerleave', () => { path.classList.remove('is-hover'); tip.hidden = true; });
        path.addEventListener('click', () => activate(active === entry ? null : entry));
        svg.append(path);
        entry.button = h('button', { type: 'button', class: 'coverage-areas__item', onclick: () => activate(active === entry ? null : entry),
          onmouseenter: () => path.classList.add('is-hover'), onmouseleave: () => path.classList.remove('is-hover') },
          h('span', { class: `coverage-dot coverage-dot--${status}`, 'aria-hidden': 'true' }),
          h('span', {}, h('strong', {}, area.name), h('small', {}, scope(area))));
        groups[status].push(entry);
        areas.set(area.name, entry);
      });
      borders = s('path', { class: 'coverage-map__borders', d: data.borders.map(l => 'M' + l.map(proj).join('L')).join('') });
      svg.append(borders);
      tip = h('div', { class: 'coverage-map__tip', hidden: true });
      canvas.append(svg, tip);

      const present = STATUSES.filter(st => groups[st].length);
      legend.replaceChildren(...present.map(st => h('button', {
        type: 'button', class: `coverage-chip coverage-chip--${st}`,
        onmouseenter: () => { svg.dataset.emphasis = st; }, onfocus: () => { svg.dataset.emphasis = st; },
        onmouseleave: () => { delete svg.dataset.emphasis; }, onblur: () => { delete svg.dataset.emphasis; }
      }, h('span', { class: 'coverage-chip__swatch', 'aria-hidden': 'true' }), T.group[st], h('small', {}, T.dioceses(groups[st].length)))));
      list.replaceChildren(...present.map(st => h('section', { class: `coverage-areas__group is-${st}` },
        h('h3', {}, `${T.group[st]} · ${T.dioceses(groups[st].length)}`),
        h('ul', {}, ...groups[st].map(entry => h('li', {}, entry.button))))));
      renderInfo(null);
      if (pending) select(...pending);
    }).catch(() => {
      canvas.textContent = T.mapError;
    });

    const select = (name, scroll) => {
      if (!svg) { pending = [name, scroll]; return; }
      const area = areas.get(name) || null;
      activate(area);
      if (area && scroll) scrollTo(figure);
    };
    return { select };
  })();

  /* The search: live as you type, with one clear verdict and a card per locality. */
  const form = section.querySelector('[data-coverage-form]');
  if (!form) return;
  const input = form.elements.query;
  const status = section.querySelector('[data-coverage-status]');
  const results = section.querySelector('[data-coverage-results]');
  // Other names people type for the provinces the place catalogue spells in one way only.
  const PROVINCE_ALIASES = { castello: ['castellon'], coruna: ['a coruna', 'la coruna'], 'araba / alava': ['alava', 'araba'],
    'illes balears': ['baleares', 'islas baleares'], bizkaia: ['vizcaya'], gipuzkoa: ['guipuzcoa'], girona: ['gerona'],
    lleida: ['lerida'], ourense: ['orense'], 'santa cruz de tenerife': ['tenerife'], alicante: ['alacant'] };
  let dataset, loading, timer, request = 0, more;

  const load = () => loading || (loading = fetch(form.dataset.url, { cache: 'no-cache' }).then(response => {
    if (!response.ok) throw new Error('Coverage unavailable');
    return response.json();
  }).then(data => {
    // Rows this page cannot read are skipped, never shown as viable; only an unreadable file is an error.
    const rows = Array.isArray(data.localities) ? data.localities.filter(row => typeof row.locality === 'string'
      && typeof row.province === 'string' && ['available', 'unavailable'].includes(row.status)) : [];
    if (!rows.length) throw new Error('Invalid coverage');
    dataset = rows.map(row => {
      const province = normalise(row.province);
      return { ...row, key: normalise(row.locality), provinceNames: [province, ...(PROVINCE_ALIASES[province] || [])] };
    });
    return dataset;
  }).catch(error => { loading = null; throw error; }));

  const counts = rows => {
    const a = rows.filter(r => r.status === 'available').length;
    return [a, rows.length - a];
  };
  const chips = rows => {
    const [a, u] = counts(rows);
    return h('span', { class: 'coverage-summary__chips' },
      a ? h('span', { class: 'coverage-chip coverage-chip--available' }, h('span', { class: 'coverage-chip__swatch', 'aria-hidden': 'true' }), T.viable(a)) : null,
      u ? h('span', { class: 'coverage-chip coverage-chip--unavailable' }, h('span', { class: 'coverage-chip__swatch', 'aria-hidden': 'true' }), T.notViable(u)) : null);
  };
  const verdict = (kind, title, meta, note, area) => {
    const action = kind === 'unavailable' ? T.writeAnyway : T.assess;
    return h('div', { class: `coverage-verdict coverage-verdict--${kind}` }, face(kind, 64),
      h('div', { class: 'coverage-verdict__body' }, badge(kind),
        h('p', { class: 'coverage-verdict__title' }, title),
        meta ? h('p', { class: 'coverage-verdict__meta' }, meta) : null,
        h('p', { class: 'coverage-verdict__note' }, note),
        h('div', { class: 'coverage-verdict__actions' },
          h('a', { class: `button ${kind === 'available' ? 'button--primary' : 'coverage-button--outline'}`, href: '#contact' }, action),
          area ? h('button', { type: 'button', class: 'coverage-link', onclick: () => map.select(area, true) }, `${T.seeMap} ↓`) : null)));
  };
  const card = row => h('li', { class: `coverage-result is-${row.status}` },
    h('button', { type: 'button', class: 'coverage-result__button', title: T.showOnMap, onclick: () => map.select(row.area, true) },
      face(row.status, 30),
      h('span', { class: 'coverage-result__text' }, h('strong', {}, row.locality), h('span', {}, `${row.province}${row.area ? ` · ${row.area}` : ''}`)),
      badge(row.status)));
  const showRows = (rows, from) => {
    const step = from ? 48 : 24;
    results.append(...rows.slice(from, from + step).map(card));
    more?.remove();
    const left = rows.length - from - step;
    if (left > 0) {
      more = h('button', { type: 'button', class: 'button coverage-more', onclick: () => showRows(rows, from + step) }, T.more(left));
      results.after(more);
    }
  };
  const reset = message => {
    results.replaceChildren();
    more?.remove();
    status.replaceChildren(h('p', { class: 'coverage-status__hint' }, message));
  };

  const run = async () => {
    const raw = input.value.trim().replace(/\s+/g, ' ');
    const query = normalise(raw);
    const current = ++request;
    if (query.length < 2) { reset(T.hint); return; }
    if (!dataset) status.replaceChildren(h('p', { class: 'coverage-status__hint' }, T.loading));
    try {
      await load();
    } catch {
      if (current === request) reset(T.error);
      return;
    }
    if (current !== request) return;
    const rank = row => row.key === query ? 0 : row.key.startsWith(query) ? 1 : row.key.includes(query) ? 2
      : row.provinceNames.some(p => p.includes(query)) ? 3 : -1;
    const ranked = dataset.map(row => [rank(row), row]).filter(([r]) => r >= 0).sort((x, y) => x[0] - y[0]
      || (x[1].status === 'available' ? 0 : 1) - (y[1].status === 'available' ? 0 : 1)
      || x[1].locality.localeCompare(y[1].locality, 'es'));
    const rows = ranked.map(([, row]) => row);
    const exact = ranked.filter(([r]) => r === 0).map(([, row]) => row);
    const province = dataset.filter(row => row.provinceNames.includes(query));
    let answer = null;
    if (exact.length && new Set(exact.map(r => r.province)).size > 1) {
      answer = verdict('mixed', T.severalProvinces(raw), null, T.noteSeveral);
    } else if (exact.length) {
      const row = exact[0];
      const place = row.locality === row.province ? row.locality : `${row.locality} (${row.province})`;
      answer = row.status === 'available'
        ? verdict('available', T.availableLocality(place), row.area, T.noteAvailable, row.area)
        : verdict('unavailable', T.unavailableLocality(place), row.area, T.noteUnavailable, row.area);
      map.select(row.area, false);
    } else if (province.length) {
      const [a, u] = counts(province);
      const name = province[0].province;
      answer = !u ? verdict('available', T.availableProvince(name), chips(province), T.noteProvince)
        : !a ? verdict('unavailable', T.unavailableProvince(name), chips(province), T.noteUnavailable)
          : verdict('mixed', T.mixedProvince(name), chips(province), T.noteProvince);
    } else if (!rows.length) {
      answer = verdict('unknown', T.unknown(raw), null, T.noteUnknown);
    }
    results.replaceChildren();
    more?.remove();
    status.replaceChildren(...[answer,
      rows.length ? h('p', { class: 'coverage-summary' }, T.matches(rows.length, raw), chips(rows)) : null].filter(Boolean));
    showRows(rows, 0);
  };

  input.setAttribute('autocomplete', 'off');
  input.addEventListener('focus', () => load().catch(() => {}), { once: true });
  input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(run, 180); });
  form.addEventListener('submit', event => {
    event.preventDefault();
    clearTimeout(timer);
    run();
  });
})();
