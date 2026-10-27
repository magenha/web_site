/* Public coverage only. No internal archive records or personal data. */
(() => {
  const form = document.querySelector('[data-coverage-form]');
  if (!form) return;
  const es = document.documentElement.lang === 'es';
  const status = document.querySelector('[data-coverage-status]');
  const results = document.querySelector('[data-coverage-results]');
  const normalise = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase().trim();
  let dataset;
  let request = 0;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const query = normalise(form.elements.query.value);
    const current = ++request;
    results.replaceChildren();
    if (!query) {
      status.textContent = es ? 'Escriba una provincia o localidad.' : 'Enter a province or locality.';
      return;
    }
    status.textContent = es ? 'Consultando cobertura…' : 'Checking coverage…';
    try {
      if (!dataset) {
        const response = await fetch(form.dataset.url);
        if (!response.ok) throw new Error('Coverage unavailable');
        const data = await response.json();
        if (!Array.isArray(data.localities) || !data.localities.every(row =>
          typeof row.locality === 'string' && typeof row.province === 'string' && row.status === 'available')) {
          throw new Error('Invalid coverage');
        }
        dataset = data.localities;
      }
      if (current !== request) return;
      const matches = dataset.filter(row => normalise(row.locality).includes(query) || normalise(row.province).includes(query));
      status.textContent = matches.length
        ? (es ? `Viabilidad disponible en ${matches.length} localidades coincidentes. Confirme la localidad exacta en la lista y solicite una evaluación individual.`
          : `Research available in ${matches.length} matching localities. Confirm the exact locality in the list and request an individual assessment.`)
        : (es ? 'Sin cobertura actual confirmada para esta consulta en los datos publicados. Compruebe el nombre o solicite una evaluación individual; esto no significa que los documentos no existan.'
          : 'No current confirmed coverage for this query in the published data. Check the name or request an individual assessment; this does not mean records do not exist.');
      for (const row of matches) {
        const item = document.createElement('li');
        item.textContent = `${row.locality} — ${row.province}`;
        results.append(item);
      }
    } catch {
      if (current !== request) return;
      status.textContent = es ? 'No se pudo consultar la cobertura. Esto no indica falta de cobertura: solicite la evaluación por correo o vuelva a intentarlo.'
        : 'Coverage could not be loaded. This does not indicate a lack of coverage: request an assessment by email or try again.';
    }
  });
})();

/* Public coverage map: area names, scope and outlines only. */
(() => {
  const figure = document.querySelector('[data-coverage-map]');
  if (!figure) return;
  const es = document.documentElement.lang === 'es';
  const canvas = figure.querySelector('[data-coverage-map-canvas]');
  const list = figure.querySelector('[data-coverage-areas]');
  const NS = 'http://www.w3.org/2000/svg';
  // Plain equirectangular grid; the Canary Islands move to an inset south-west of the peninsula.
  const K = Math.cos(40 * Math.PI / 180);
  const proj = ([lon, lat]) => {
    if (lon < -13 && lat < 30) { lon += 6.2; lat += 7; }
    return `${((lon + 12.5) * K * 60).toFixed(1)},${((44.2 - lat) * 60).toFixed(1)}`;
  };
  const W = Math.ceil(17.1 * K * 60), H = Math.ceil(9.8 * 60);
  const scope = area => area.scope.map(p => p.whole ? p.province
    : p.places.length ? `${p.province}: ${p.places.join(', ')}`
      : `${p.province} (${p.municipalities} ${es ? 'de' : 'of'} ${p.total} ${es ? 'municipios' : 'municipalities'})`).join('; ');
  const el = (name, attrs) => {
    const node = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    return node;
  };
  fetch(figure.dataset.url).then(r => { if (!r.ok) throw new Error('Map unavailable'); return r.json(); }).then(data => {
    if (!Array.isArray(data.areas) || !Array.isArray(data.borders)) throw new Error('Invalid map');
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': figure.getAttribute('aria-label') });
    const a = proj([-18.4, 29.5]).split(','), b = proj([-13.2, 27.5]).split(',');
    svg.append(el('rect', { class: 'coverage-map__inset', x: a[0], y: a[1], width: b[0] - a[0], height: b[1] - a[1] }));
    const paths = [], items = [];
    const activate = i => {
      paths.forEach((p, k) => p.classList.toggle('is-active', k === i));
      items.forEach((li, k) => li.classList.toggle('is-active', k === i));
    };
    data.areas.forEach((area, i) => {
      const d = area.polygons.map(poly => poly.map(ring => 'M' + ring.map(proj).join('L') + 'Z').join('')).join('');
      const path = el('path', { d, class: 'coverage-map__area' + (area.status === 'limited' ? ' is-limited' : '') });
      const title = el('title', {});
      title.textContent = `${area.name} — ${scope(area)}`;
      path.append(title);
      path.addEventListener('mouseenter', () => activate(i));
      path.addEventListener('mouseleave', () => activate(-1));
      path.addEventListener('click', () => activate(i));
      svg.append(path); paths.push(path);
      const li = document.createElement('li');
      const name = document.createElement('strong');
      name.textContent = area.name;
      li.append(name, document.createTextNode(` — ${scope(area)}`));
      li.addEventListener('mouseenter', () => activate(i));
      li.addEventListener('mouseleave', () => activate(-1));
      list.append(li); items.push(li);
    });
    svg.append(el('path', { class: 'coverage-map__borders', d: data.borders.map(l => 'M' + l.map(proj).join('L')).join('') }));
    canvas.append(svg);
  }).catch(() => {
    canvas.textContent = es ? 'No se pudo cargar el mapa. Use el buscador o solicite una evaluación por correo.'
      : 'The map could not be loaded. Use the search or request an assessment by email.';
  });
})();
