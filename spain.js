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
