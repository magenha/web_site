(() => {
  "use strict";

  const app = document.querySelector("[data-statistics-app]");
  if (!app) return;

  const language = app.dataset.language === "es" ? "es" : "en";
  const locale = language === "es" ? "es-ES" : "en-US";
  const integerFormat = new Intl.NumberFormat(locale);
  const percentageFormat = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  });
  const collator = new Intl.Collator(locale, { numeric: true, sensitivity: "base" });

  const copy = language === "es" ? {
    loadError: "No se pudieron cargar los datos estadísticos locales. Inténtelo de nuevo más tarde.",
    fileError: "Este explorador debe abrirse desde un servidor web. Para una vista local, ejecute «python3 -m http.server» en la carpeta web_site.",
    invalidData: "El archivo de estadísticas no tiene el formato esperado.",
    observations: (count) => `${observationCountLabel(count)} de origen; debajo se muestran solo celdas publicables`,
    noObservations: "No hay observaciones de este tipo.",
    privacyUnavailable: (count, minimum) => `${observationCountLabel(count)} de origen; el desglose no se publica por debajo de ${integerFormat.format(minimum)}`,
    privacyNotice: (parts, minimum) => `Control de privacidad: no se publica el desglose de ${parts.join("; ")} porque no alcanza ${integerFormat.format(minimum)} observaciones del mismo tipo.`,
    ySample: (count) => `ADN-Y: ${integerFormat.format(count)}`,
    mtSample: (count) => `ADNmt: ${integerFormat.format(count)}`,
    emptyTable: "No hay celdas publicadas para este perfil",
    countryGroupTable: (type, name) => `Grupos principales de ${type} publicados para ${name}`,
    countryHaplogroupTable: (type, name) => `Haplogrupos detallados de ${type} publicados para ${name}`,
    paternal: "ADN-Y · línea paterna",
    maternal: "ADNmt · línea materna",
    exact: "Haplogrupo detallado",
    group: "Grupo principal",
    noEligibleCountries: "Ningún país alcanza el mínimo de observaciones seleccionado.",
    noMatchingCountries: "No hay coincidencias publicadas entre los países que alcanzan el mínimo de observaciones.",
    resultSummary: (matching, eligible, threshold) => `${integerFormat.format(matching)} de ${integerFormat.format(eligible)} países con al menos ${integerFormat.format(threshold)} observaciones contienen coincidencias publicadas. El porcentaje usa únicamente observaciones del mismo tipo de ADN.`,
    countryCaption: (value, type, threshold) => `Coincidencias publicadas de ${value} · ${type} · países con al menos ${integerFormat.format(threshold)} observaciones`,
    tooltipResult: (matching, sample, share) => `${integerFormat.format(matching)} de ${integerFormat.format(sample)} · ${formatPercentage(share)}`,
    noPublishedMatch: (sample) => `${observationCountLabel(sample)}; sin coincidencia publicada (cero o valor oculto)`,
    belowThreshold: (sample, threshold) => `${observationCountLabel(sample)}; por debajo del mínimo de ${integerFormat.format(threshold)}`,
    privacyBelowThreshold: (sample, threshold) => `${observationCountLabel(sample)}; desglose oculto por debajo del mínimo de privacidad de ${integerFormat.format(threshold)}`,
    noTypeData: "Sin observaciones de este tipo",
    privacySummary: (countryMinimum, cellMinimum) => `Control de divulgación: se publican desgloses a partir de ${integerFormat.format(countryMinimum)} observaciones del mismo tipo y celdas a partir de ${integerFormat.format(cellMinimum)}; también pueden ocultarse celdas complementarias.`,
    distributionTitle: (value) => `Distribución de ${value}`,
    mapTitle: (value, type) => `Mapa de distribución de ${value} (${type})`,
    mapEntryLabel: (name, value, type, detail) => `${name}. ${value}, ${type}: ${detail}`
  } : {
    loadError: "The local statistics files could not be loaded. Please try again later.",
    fileError: "This explorer must be opened through a web server. For a local preview, run “python3 -m http.server” inside the web_site folder.",
    invalidData: "The statistics file does not have the expected format.",
    observations: (count) => `${observationCountLabel(count)} in the source; only publishable cells appear below`,
    noObservations: "No observations of this type.",
    privacyUnavailable: (count, minimum) => `${observationCountLabel(count)} in the source; breakdown not published below ${integerFormat.format(minimum)}`,
    privacyNotice: (parts, minimum) => `Privacy control: no breakdown is published for ${parts.join("; ")} because it does not reach ${integerFormat.format(minimum)} same-type observations.`,
    ySample: (count) => `Y-DNA: ${integerFormat.format(count)}`,
    mtSample: (count) => `mtDNA: ${integerFormat.format(count)}`,
    emptyTable: "No cells are published for this profile",
    countryGroupTable: (type, name) => `Published ${type} major groups for ${name}`,
    countryHaplogroupTable: (type, name) => `Published detailed ${type} haplogroups for ${name}`,
    paternal: "Y-DNA · paternal line",
    maternal: "mtDNA · maternal line",
    exact: "Detailed haplogroup",
    group: "Major group",
    noEligibleCountries: "No countries reach the selected observation minimum.",
    noMatchingCountries: "No published matches appear among countries reaching the observation minimum.",
    resultSummary: (matching, eligible, threshold) => `${integerFormat.format(matching)} of ${integerFormat.format(eligible)} countries with at least ${integerFormat.format(threshold)} observations contain published matches. The percentage uses only observations of the same DNA type.`,
    countryCaption: (value, type, threshold) => `Published ${value} matches · ${type} · countries with at least ${integerFormat.format(threshold)} observations`,
    tooltipResult: (matching, sample, share) => `${integerFormat.format(matching)} of ${integerFormat.format(sample)} · ${formatPercentage(share)}`,
    noPublishedMatch: (sample) => `${observationCountLabel(sample)}; no published match (zero or withheld)`,
    belowThreshold: (sample, threshold) => `${observationCountLabel(sample)}; below the ${integerFormat.format(threshold)} minimum`,
    privacyBelowThreshold: (sample, threshold) => `${observationCountLabel(sample)}; breakdown withheld below the privacy minimum of ${integerFormat.format(threshold)}`,
    noTypeData: "No observations of this type",
    privacySummary: (countryMinimum, cellMinimum) => `Disclosure control: breakdowns start at ${integerFormat.format(countryMinimum)} same-type observations and cells at ${integerFormat.format(cellMinimum)}; complementary cells may also be withheld.`,
    distributionTitle: (value) => `${value} distribution`,
    mapTitle: (value, type) => `${value} (${type}) distribution map`,
    mapEntryLabel: (name, value, type, detail) => `${name}. ${value}, ${type}: ${detail}`
  };

  const elements = {
    status: app.querySelector("[data-statistics-status]"),
    content: app.querySelector("[data-statistics-content]"),
    summaryObservations: app.querySelector("[data-summary-observations]"),
    summaryCountries: app.querySelector("[data-summary-countries]"),
    summaryHaplogroups: app.querySelector("[data-summary-haplogroups]"),
    countrySelect: app.querySelector("[data-country-select]"),
    countryCode: app.querySelector("[data-country-code]"),
    countryName: app.querySelector("[data-country-name]"),
    countryYTotal: app.querySelector("[data-country-y-total]"),
    countryMtTotal: app.querySelector("[data-country-mt-total]"),
    countryNotice: app.querySelector("[data-country-notice]"),
    lineageType: app.querySelector("[data-lineage-type]"),
    lineageLevel: app.querySelector("[data-lineage-level]"),
    haplogroupSelect: app.querySelector("[data-haplogroup-select]"),
    groupSelect: app.querySelector("[data-group-select]"),
    threshold: app.querySelector("[data-sample-threshold]"),
    distributionForm: app.querySelector("[data-distribution-form]"),
    distributionKicker: app.querySelector("[data-distribution-kicker]"),
    distributionTitle: app.querySelector("[data-distribution-title]"),
    distributionSummary: app.querySelector("[data-distribution-summary]"),
    distributionCaption: app.querySelector("[data-distribution-caption]"),
    distributionRows: app.querySelector("[data-distribution-rows]"),
    distributionEmpty: app.querySelector("[data-distribution-empty]"),
    map: app.querySelector("[data-world-map]"),
    mapFrame: app.querySelector("[data-map-frame]"),
    mapPolygons: app.querySelector("[data-map-polygons]"),
    mapMarkers: app.querySelector("[data-map-markers]"),
    mapTooltip: app.querySelector("[data-map-tooltip]"),
    mapTitle: app.querySelector("#map-title"),
    methodologySource: app.querySelector("[data-methodology-source]")
  };

  const state = {
    data: null,
    countries: [],
    countryByCode: new Map(),
    countryCounts: new Map(),
    exactDistribution: new Map(),
    groupDistribution: new Map(),
    polygonElements: new Map(),
    markerElements: new Map(),
    interactiveMapElements: new Map(),
    polygonCodes: new Set(),
    mapResults: new Map(),
    mapThreshold: 30,
    privacyCountryMinimum: 30,
    privacyCellMinimum: 5,
    mapSelection: null
  };

  function formatPercentage(value) {
    const suffix = language === "es" ? " %" : "%";
    return `${percentageFormat.format(value)}${suffix}`;
  }

  function observationCountLabel(value) {
    const count = Number(value);
    const noun = language === "es"
      ? (count === 1 ? "observación" : "observaciones")
      : (count === 1 ? "observation" : "observations");
    return `${integerFormat.format(count)} ${noun}`;
  }

  function countryName(country) {
    return country?.names?.[language] || country?.names?.en || country?.alpha2 || "—";
  }

  function lineageTypeLabel(type) {
    if (type === "YDNA") return language === "es" ? "ADN-Y" : "Y-DNA";
    return language === "es" ? "ADNmt" : "mtDNA";
  }

  function mapFor(container, key) {
    if (!container.has(key)) container.set(key, new Map());
    return container.get(key);
  }

  function distributionKey(type, value) {
    return `${type}\u0000${value}`;
  }

  function countryTypeKey(alpha2, type) {
    return `${alpha2}\u0000${type}`;
  }

  function indexData(data) {
    const expectedColumns = ["type", "haplogroup", "group", "alpha2", "count"];
    const expectedGroupColumns = ["type", "group", "alpha2", "count"];
    if (
      !data ||
      data.schema_version !== 2 ||
      !Array.isArray(data.countries) ||
      !Array.isArray(data.observations) ||
      !Array.isArray(data.observation_columns) ||
      !expectedColumns.every((column) => data.observation_columns.includes(column)) ||
      !Array.isArray(data.group_observations) ||
      !Array.isArray(data.group_observation_columns) ||
      !expectedGroupColumns.every((column) => data.group_observation_columns.includes(column))
    ) {
      throw new Error(copy.invalidData);
    }

    const column = Object.fromEntries(data.observation_columns.map((name, index) => [name, index]));
    const groupColumn = Object.fromEntries(data.group_observation_columns.map((name, index) => [name, index]));
    state.data = data;
    state.privacyCountryMinimum = Number(data.privacy?.minimum_country_type_observation_count || 30);
    state.privacyCellMinimum = Number(data.privacy?.minimum_cell_count || 5);
    state.countries = [...data.countries].sort((a, b) => collator.compare(countryName(a), countryName(b)));
    state.countryByCode = new Map(state.countries.map((country) => [country.alpha2, country]));

    data.observations.forEach((observation) => {
      const type = observation[column.type];
      const haplogroup = observation[column.haplogroup];
      const group = observation[column.group];
      const alpha2 = observation[column.alpha2];
      const count = Number(observation[column.count]);

      if (!state.countryByCode.has(alpha2) || !Number.isFinite(count) || count <= 0) return;

      const countryCounts = mapFor(state.countryCounts, countryTypeKey(alpha2, type));
      countryCounts.set(`haplogroup\u0000${haplogroup}`, count);

      const exact = mapFor(state.exactDistribution, distributionKey(type, haplogroup));
      exact.set(alpha2, (exact.get(alpha2) || 0) + count);
    });

    data.group_observations.forEach((observation) => {
      const type = observation[groupColumn.type];
      const group = observation[groupColumn.group];
      const alpha2 = observation[groupColumn.alpha2];
      const count = Number(observation[groupColumn.count]);

      if (!state.countryByCode.has(alpha2) || !Number.isFinite(count) || count <= 0) return;

      const countryCounts = mapFor(state.countryCounts, countryTypeKey(alpha2, type));
      countryCounts.set(`group\u0000${group}`, count);
      const grouped = mapFor(state.groupDistribution, distributionKey(type, group));
      grouped.set(alpha2, (grouped.get(alpha2) || 0) + count);
    });
  }

  function populateSelect(select, values, preferredValue) {
    select.replaceChildren();
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.append(option);
    });
    if (values.includes(preferredValue)) select.value = preferredValue;
  }

  function totalForValue(type, level, value) {
    const source = level === "group" ? state.groupDistribution : state.exactDistribution;
    return [...(source.get(distributionKey(type, value))?.values() || [])]
      .reduce((sum, count) => sum + count, 0);
  }

  function mostFrequentValue(type, level) {
    const values = state.data[level === "group" ? "groups" : "haplogroups"]?.[type] || [];
    return [...values].sort((a, b) => {
      const difference = totalForValue(type, level, b) - totalForValue(type, level, a);
      return difference || collator.compare(a, b);
    })[0] || "";
  }

  function setLineageOptions(preferredHaplogroup, preferredGroup) {
    const type = elements.lineageType.value;
    const haplogroups = state.data.haplogroups?.[type] || [];
    const groups = state.data.groups?.[type] || [];
    populateSelect(
      elements.haplogroupSelect,
      haplogroups,
      haplogroups.includes(preferredHaplogroup) ? preferredHaplogroup : mostFrequentValue(type, "haplogroup")
    );
    populateSelect(
      elements.groupSelect,
      groups,
      groups.includes(preferredGroup) ? preferredGroup : mostFrequentValue(type, "group")
    );
  }

  function populateControls() {
    elements.countrySelect.replaceChildren();
    state.countries.forEach((country) => {
      const option = document.createElement("option");
      option.value = country.alpha2;
      option.textContent = countryName(country);
      elements.countrySelect.append(option);
    });

    const thresholdOptions = [...elements.threshold.options]
      .filter((option) => Number(option.value) >= state.privacyCountryMinimum);
    if (!thresholdOptions.length) {
      const option = document.createElement("option");
      option.value = String(state.privacyCountryMinimum);
      option.textContent = `${integerFormat.format(state.privacyCountryMinimum)} ${language === "es" ? "observaciones" : "observations"}`;
      elements.threshold.replaceChildren(option);
    } else {
      [...elements.threshold.options].forEach((option) => {
        if (Number(option.value) < state.privacyCountryMinimum) option.remove();
      });
    }

    [
      elements.countrySelect,
      elements.lineageType,
      elements.lineageLevel,
      elements.haplogroupSelect,
      elements.groupSelect,
      elements.threshold
    ].forEach((control) => { control.disabled = false; });
  }

  function applyInitialState() {
    const params = new URLSearchParams(window.location.search);
    const requestedCountry = params.get("country")?.toUpperCase();
    const defaultCountry = state.countryByCode.has("CU")
      ? "CU"
      : [...state.countries].sort((a, b) => b.observation_counts.total - a.observation_counts.total)[0]?.alpha2;
    elements.countrySelect.value = state.countryByCode.has(requestedCountry) ? requestedCountry : defaultCountry;

    const requestedType = params.get("type");
    elements.lineageType.value = ["YDNA", "mtDNA"].includes(requestedType) ? requestedType : "YDNA";
    const requestedLevel = params.get("level");
    elements.lineageLevel.value = ["haplogroup", "group"].includes(requestedLevel) ? requestedLevel : "haplogroup";

    const requestedThreshold = params.get("min");
    const availableThresholds = [...elements.threshold.options].map((option) => option.value);
    const defaultThreshold = availableThresholds.includes(String(state.privacyCountryMinimum))
      ? String(state.privacyCountryMinimum)
      : availableThresholds[0];
    elements.threshold.value = availableThresholds.includes(requestedThreshold)
      ? requestedThreshold
      : defaultThreshold;

    const requestedValue = params.get("lineage") || "";
    setLineageOptions(
      elements.lineageLevel.value === "haplogroup" ? requestedValue : "",
      elements.lineageLevel.value === "group" ? requestedValue : ""
    );
    updateVisibleLineageSelector();
  }

  function frequencyEntries(alpha2, type, level) {
    const counts = state.countryCounts.get(countryTypeKey(alpha2, type)) || new Map();
    const prefix = `${level}\u0000`;
    return [...counts.entries()]
      .filter(([key]) => key.startsWith(prefix))
      .map(([key, count]) => ({ value: key.slice(prefix.length), count }))
      .sort((a, b) => b.count - a.count || collator.compare(a.value, b.value));
  }

  function appendEmptyRow(tbody) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 3;
    cell.className = "statistics-table__empty";
    cell.textContent = copy.emptyTable;
    row.append(cell);
    tbody.append(row);
  }

  function renderFrequencyTable(tbody, entries, total) {
    tbody.replaceChildren();
    if (!entries.length || !total) {
      appendEmptyRow(tbody);
      return;
    }

    entries.forEach(({ value, count }) => {
      const share = count / total * 100;
      const row = document.createElement("tr");
      const label = document.createElement("td");
      const countCell = document.createElement("td");
      const shareCell = document.createElement("td");
      label.className = "statistics-table__label";
      shareCell.className = "statistics-table__bar";
      shareCell.style.setProperty("--share", `${Math.min(100, share)}%`);
      label.textContent = value;
      countCell.textContent = integerFormat.format(count);
      shareCell.textContent = formatPercentage(share);
      row.append(label, countCell, shareCell);
      tbody.append(row);
    });
  }

  function renderCountry() {
    const country = state.countryByCode.get(elements.countrySelect.value);
    if (!country) return;

    const displayName = countryName(country);
    const yTotal = Number(country.observation_counts.YDNA || 0);
    const mtTotal = Number(country.observation_counts.mtDNA || 0);
    elements.countryCode.textContent = country.alpha2;
    elements.countryName.textContent = displayName;
    elements.countryYTotal.textContent = integerFormat.format(yTotal);
    elements.countryMtTotal.textContent = integerFormat.format(mtTotal);

    ["YDNA", "mtDNA"].forEach((type) => {
      const total = Number(country.observation_counts[type] || 0);
      const typeLabel = lineageTypeLabel(type);
      const summary = app.querySelector(`[data-country-type-summary="${type}"]`);
      const groupCaption = app.querySelector(`[data-country-table-caption="${type}-group"]`);
      const haplogroupCaption = app.querySelector(`[data-country-table-caption="${type}-haplogroup"]`);
      summary.textContent = !total
        ? copy.noObservations
        : total < state.privacyCountryMinimum
          ? copy.privacyUnavailable(total, state.privacyCountryMinimum)
          : copy.observations(total);
      groupCaption.textContent = copy.countryGroupTable(typeLabel, displayName);
      haplogroupCaption.textContent = copy.countryHaplogroupTable(typeLabel, displayName);
      renderFrequencyTable(
        app.querySelector(`[data-country-groups="${type}"]`),
        frequencyEntries(country.alpha2, type, "group"),
        total
      );
      renderFrequencyTable(
        app.querySelector(`[data-country-haplogroups="${type}"]`),
        frequencyEntries(country.alpha2, type, "haplogroup"),
        total
      );
    });

    const unavailableBreakdowns = [];
    if (yTotal > 0 && yTotal < state.privacyCountryMinimum) unavailableBreakdowns.push(copy.ySample(yTotal));
    if (mtTotal > 0 && mtTotal < state.privacyCountryMinimum) unavailableBreakdowns.push(copy.mtSample(mtTotal));
    elements.countryNotice.hidden = unavailableBreakdowns.length === 0;
    elements.countryNotice.textContent = unavailableBreakdowns.length
      ? copy.privacyNotice(unavailableBreakdowns, state.privacyCountryMinimum)
      : "";
  }

  function project([longitude, latitude]) {
    return [
      (Number(longitude) + 180) / 360 * 1000,
      (90 - Number(latitude)) / 180 * 500 + 5
    ];
  }

  function ringPath(ring) {
    return ring.map((point, index) => {
      const [x, y] = project(point);
      return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
    }).join("") + "Z";
  }

  function geometryPath(geometry) {
    if (!geometry || !Array.isArray(geometry.coordinates)) return "";
    if (geometry.type === "Polygon") {
      return geometry.coordinates.map(ringPath).join("");
    }
    if (geometry.type === "MultiPolygon") {
      return geometry.coordinates.flatMap((polygon) => polygon.map(ringPath)).join("");
    }
    return "";
  }

  function registerMapElement(collection, alpha2, element) {
    if (!alpha2 || !state.countryByCode.has(alpha2)) return;
    if (!collection.has(alpha2)) collection.set(alpha2, []);
    collection.get(alpha2).push(element);
  }

  function bindTooltip(element, alpha2) {
    const initialName = countryName(state.countryByCode.get(alpha2));
    element.setAttribute("tabindex", "0");
    element.setAttribute("role", "button");
    element.setAttribute("aria-label", initialName);
    registerMapElement(state.interactiveMapElements, alpha2, element);

    element.addEventListener("pointermove", (event) => showMapTooltip(event, alpha2));
    element.addEventListener("pointerdown", (event) => {
      if (event.pointerType === "mouse") return;
      focusMapElement(element);
      showMapTooltip(event, alpha2);
    });
    element.addEventListener("pointerleave", () => {
      if (document.activeElement !== element) hideMapTooltip();
    });
    element.addEventListener("focus", () => showMapTooltipForElement(element, alpha2));
    element.addEventListener("blur", hideMapTooltip);
    element.addEventListener("click", (event) => {
      focusMapElement(element);
      showMapTooltip(event, alpha2);
    });
    element.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        hideMapTooltip();
        element.blur();
        return;
      }
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      showMapTooltipForElement(element, alpha2);
    });
  }

  function renderMapGeometry(geojson) {
    if (!geojson || geojson.type !== "FeatureCollection" || !Array.isArray(geojson.features)) {
      throw new Error(copy.invalidData);
    }

    const namespace = "http://www.w3.org/2000/svg";
    const polygonFragment = document.createDocumentFragment();

    geojson.features.forEach((feature) => {
      const pathData = geometryPath(feature.geometry);
      if (!pathData) return;
      const alpha2 = feature.properties?.alpha2 || "";
      const path = document.createElementNS(namespace, "path");
      path.setAttribute("d", pathData);
      path.setAttribute("fill-rule", "evenodd");
      path.setAttribute("class", "world-map__country");
      path.dataset.country = alpha2;
      if (alpha2 && state.countryByCode.has(alpha2)) {
        state.polygonCodes.add(alpha2);
        registerMapElement(state.polygonElements, alpha2, path);
        bindTooltip(path, alpha2);
        const title = document.createElementNS(namespace, "title");
        title.textContent = countryName(state.countryByCode.get(alpha2));
        path.append(title);
      } else {
        path.setAttribute("aria-hidden", "true");
      }
      polygonFragment.append(path);
    });

    elements.mapPolygons.replaceChildren(polygonFragment);

    const markerFragment = document.createDocumentFragment();
    state.countries
      .filter((country) => !state.polygonCodes.has(country.alpha2) && Array.isArray(country.marker))
      .forEach((country) => {
        const [x, y] = project(country.marker);
        const markerGroup = document.createElementNS(namespace, "g");
        const halo = document.createElementNS(namespace, "circle");
        const marker = document.createElementNS(namespace, "circle");
        const title = document.createElementNS(namespace, "title");
        markerGroup.setAttribute("class", "world-map__marker-control");
        markerGroup.dataset.country = country.alpha2;
        halo.setAttribute("class", "world-map__marker-halo");
        halo.setAttribute("cx", x.toFixed(2));
        halo.setAttribute("cy", y.toFixed(2));
        halo.setAttribute("r", "5.5");
        marker.setAttribute("class", "world-map__marker");
        marker.setAttribute("cx", x.toFixed(2));
        marker.setAttribute("cy", y.toFixed(2));
        marker.setAttribute("r", "3.25");
        title.textContent = countryName(country);
        markerGroup.append(halo, marker, title);
        bindTooltip(markerGroup, country.alpha2);
        registerMapElement(state.markerElements, country.alpha2, marker);
        markerFragment.append(markerGroup);
      });
    elements.mapMarkers.replaceChildren(markerFragment);
  }

  function mixColor(start, end, ratio) {
    const value = Math.max(0, Math.min(1, ratio));
    const channels = start.map((channel, index) => Math.round(channel + (end[index] - channel) * value));
    return `rgb(${channels.join(", ")})`;
  }

  function resultColor(share, maximum) {
    if (!maximum || share <= 0) return "#d8ece8";
    const position = Math.sqrt(share / maximum);
    if (position < 0.55) return mixColor([216, 236, 232], [11, 123, 127], position / 0.55);
    return mixColor([11, 123, 127], [23, 63, 65], (position - 0.55) / 0.45);
  }

  function selectedDistribution() {
    const type = elements.lineageType.value;
    const level = elements.lineageLevel.value;
    const value = level === "group" ? elements.groupSelect.value : elements.haplogroupSelect.value;
    const source = level === "group" ? state.groupDistribution : state.exactDistribution;
    return { type, level, value, counts: source.get(distributionKey(type, value)) || new Map() };
  }

  function distributionRows(selection, threshold) {
    return state.countries.map((country) => {
      const sample = Number(country.observation_counts[selection.type] || 0);
      const published = selection.counts.has(country.alpha2);
      const matching = Number(selection.counts.get(country.alpha2) || 0);
      return {
        country,
        sample,
        matching,
        published,
        eligible: sample >= Math.max(threshold, state.privacyCountryMinimum),
        share: published && sample ? matching / sample * 100 : 0
      };
    });
  }

  function renderDistributionTable(rows, selection, threshold) {
    const matchingRows = rows
      .filter((row) => row.eligible && row.published)
      .sort((a, b) => b.share - a.share || b.matching - a.matching || collator.compare(countryName(a.country), countryName(b.country)));

    elements.distributionRows.replaceChildren();
    matchingRows.forEach((result) => {
      const row = document.createElement("tr");
      const nameCell = document.createElement("td");
      const matchingCell = document.createElement("td");
      const sampleCell = document.createElement("td");
      const shareCell = document.createElement("td");
      const name = document.createElement("span");
      const code = document.createElement("small");
      name.className = "statistics-table__label";
      code.className = "statistics-table__country-code";
      name.textContent = countryName(result.country);
      code.textContent = result.country.alpha2;
      nameCell.append(name, code);
      matchingCell.textContent = integerFormat.format(result.matching);
      sampleCell.textContent = integerFormat.format(result.sample);
      shareCell.className = "statistics-table__bar";
      shareCell.style.setProperty("--share", `${Math.min(100, result.share)}%`);
      shareCell.textContent = formatPercentage(result.share);
      row.append(nameCell, matchingCell, sampleCell, shareCell);
      elements.distributionRows.append(row);
    });

    elements.distributionEmpty.hidden = matchingRows.length > 0;
    if (!matchingRows.length) {
      elements.distributionEmpty.textContent = rows.some((row) => row.eligible)
        ? copy.noMatchingCountries
        : copy.noEligibleCountries;
    }
    const typeLabel = lineageTypeLabel(selection.type);
    elements.distributionCaption.textContent = copy.countryCaption(selection.value, typeLabel, threshold);
    return matchingRows.length;
  }

  function updateMap(rows, threshold, selection) {
    const maximum = Math.max(0, ...rows.filter((row) => row.eligible && row.published).map((row) => row.share));
    state.mapResults = new Map(rows.map((row) => [row.country.alpha2, row]));
    state.mapThreshold = threshold;
    state.mapSelection = selection;

    state.countries.forEach((country) => {
      const result = state.mapResults.get(country.alpha2);
      const hasPublishedResult = Boolean(result?.eligible && result?.published);
      const fill = hasPublishedResult ? resultColor(result.share, maximum) : "#eee8dc";
      (state.polygonElements.get(country.alpha2) || []).forEach((path) => {
        path.style.fill = fill;
        path.dataset.hasResult = String(hasPublishedResult);
      });
      (state.markerElements.get(country.alpha2) || []).forEach((marker) => {
        marker.style.fill = hasPublishedResult ? resultColor(result.share, maximum) : "#a9aaa3";
        marker.style.opacity = result?.sample ? "1" : "0.45";
      });
      const text = tooltipText(country.alpha2);
      const accessibleLabel = text
        ? copy.mapEntryLabel(text.name, selection.value, lineageTypeLabel(selection.type), text.detail)
        : countryName(country);
      (state.interactiveMapElements.get(country.alpha2) || []).forEach((element) => {
        element.setAttribute("aria-label", accessibleLabel);
        const title = element.querySelector("title");
        if (title) title.textContent = accessibleLabel;
      });
    });
  }

  function renderDistribution() {
    const selection = selectedDistribution();
    if (!selection.value) return;
    const threshold = Number(elements.threshold.value);
    const rows = distributionRows(selection, threshold);
    const eligible = rows.filter((row) => row.eligible).length;
    const matching = renderDistributionTable(rows, selection, threshold);
    elements.distributionKicker.textContent = `${selection.type === "YDNA" ? copy.paternal : copy.maternal} · ${selection.level === "group" ? copy.group : copy.exact}`;
    elements.distributionTitle.textContent = copy.distributionTitle(selection.value);
    elements.distributionSummary.textContent = copy.resultSummary(matching, eligible, threshold);
    elements.mapTitle.textContent = copy.mapTitle(selection.value, lineageTypeLabel(selection.type));
    updateMap(rows, threshold, selection);
  }

  function tooltipText(alpha2) {
    const country = state.countryByCode.get(alpha2);
    const result = state.mapResults.get(alpha2);
    if (!country || !result) return null;
    if (!result.sample) return { name: countryName(country), detail: copy.noTypeData };
    if (result.sample < state.privacyCountryMinimum) {
      return {
        name: countryName(country),
        detail: copy.privacyBelowThreshold(result.sample, state.privacyCountryMinimum)
      };
    }
    if (!result.eligible) {
      return { name: countryName(country), detail: copy.belowThreshold(result.sample, state.mapThreshold) };
    }
    return {
      name: countryName(country),
      detail: result.published
        ? copy.tooltipResult(result.matching, result.sample, result.share)
        : copy.noPublishedMatch(result.sample)
    };
  }

  function focusMapElement(element) {
    if (document.activeElement === element) return;
    try {
      element.focus({ preventScroll: true });
    } catch {
      element.focus();
    }
  }

  function showMapTooltipAt(clientX, clientY, alpha2) {
    const text = tooltipText(alpha2);
    if (!text) return;
    const frame = elements.mapFrame.getBoundingClientRect();
    const title = document.createElement("strong");
    const detail = document.createElement("span");
    title.textContent = text.name;
    detail.textContent = text.detail;
    elements.mapTooltip.replaceChildren(title, detail);
    elements.mapTooltip.classList.remove("map-tooltip--below");
    elements.mapTooltip.style.left = `${clientX - frame.left + elements.mapFrame.scrollLeft}px`;
    elements.mapTooltip.style.top = `${clientY - frame.top + elements.mapFrame.scrollTop}px`;
    elements.mapTooltip.hidden = false;

    const padding = 8;
    const translatedGap = 12;
    const minimumLeft = elements.mapFrame.scrollLeft + padding;
    const maximumLeft = Math.max(
      minimumLeft,
      elements.mapFrame.scrollLeft + elements.mapFrame.clientWidth - elements.mapTooltip.offsetWidth - translatedGap - padding
    );
    const proposedLeft = clientX - frame.left + elements.mapFrame.scrollLeft;
    elements.mapTooltip.style.left = `${Math.max(minimumLeft, Math.min(maximumLeft, proposedLeft))}px`;
    if (clientY - frame.top < elements.mapTooltip.offsetHeight + translatedGap + padding) {
      elements.mapTooltip.classList.add("map-tooltip--below");
    }
  }

  function showMapTooltip(event, alpha2) {
    showMapTooltipAt(event.clientX, event.clientY, alpha2);
  }

  function showMapTooltipForElement(element, alpha2) {
    const bounds = element.getBoundingClientRect();
    showMapTooltipAt(bounds.left + bounds.width / 2, bounds.top + bounds.height / 2, alpha2);
  }

  function hideMapTooltip() {
    elements.mapTooltip.hidden = true;
  }

  function updateVisibleLineageSelector() {
    const level = elements.lineageLevel.value;
    app.querySelectorAll("[data-lineage-selector-wrap]").forEach((wrapper) => {
      wrapper.hidden = wrapper.dataset.lineageSelectorWrap !== level;
    });
  }

  function updateUrl() {
    const selection = selectedDistribution();
    const params = new URLSearchParams();
    params.set("country", elements.countrySelect.value);
    params.set("type", selection.type);
    params.set("level", selection.level);
    params.set("lineage", selection.value);
    params.set("min", elements.threshold.value);
    const query = params.toString();
    const nextUrl = `${window.location.pathname}?${query}${window.location.hash}`;
    window.history.replaceState(null, "", nextUrl);

    document.querySelectorAll("a[hreflang]").forEach((link) => {
      const target = new URL(link.href);
      if (!target.pathname.endsWith("statistics.html")) return;
      target.search = query;
      target.hash = window.location.hash;
      link.href = target.toString();
    });
  }

  function bindControls() {
    elements.distributionForm.addEventListener("submit", (event) => event.preventDefault());

    elements.countrySelect.addEventListener("change", () => {
      renderCountry();
      updateUrl();
    });

    elements.lineageType.addEventListener("change", () => {
      setLineageOptions("", "");
      renderDistribution();
      updateUrl();
    });

    elements.lineageLevel.addEventListener("change", () => {
      updateVisibleLineageSelector();
      renderDistribution();
      updateUrl();
    });

    [elements.haplogroupSelect, elements.groupSelect, elements.threshold].forEach((control) => {
      control.addEventListener("change", () => {
        renderDistribution();
        updateUrl();
      });
    });
  }

  function renderSummary() {
    const totals = state.data.totals || {};
    const haplogroupCount = Object.values(state.data.haplogroups || {})
      .reduce((sum, values) => sum + values.length, 0);
    elements.summaryObservations.textContent = integerFormat.format(totals.observation_count || 0);
    elements.summaryCountries.textContent = integerFormat.format(totals.country_count || state.countries.length);
    elements.summaryHaplogroups.textContent = integerFormat.format(haplogroupCount);

    if (elements.methodologySource) {
      elements.methodologySource.textContent = copy.privacySummary(
        state.privacyCountryMinimum,
        state.privacyCellMinimum
      );
      elements.methodologySource.hidden = false;
    }
  }

  function showError(error) {
    console.error("MAGENHA statistics explorer:", error);
    elements.content.hidden = true;
    elements.status.hidden = false;
    elements.status.dataset.state = "error";
    const message = window.location.protocol === "file:" ? copy.fileError : (error?.message || copy.loadError);
    elements.status.querySelector("p").textContent = message;
  }

  async function fetchJson(url) {
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(copy.loadError);
    return response.json();
  }

  async function initialize() {
    try {
      const [data, geojson] = await Promise.all([
        fetchJson(app.dataset.statisticsUrl),
        fetchJson(app.dataset.mapUrl)
      ]);
      indexData(data);
      populateControls();
      applyInitialState();
      renderMapGeometry(geojson);
      renderSummary();
      bindControls();
      renderCountry();
      renderDistribution();
      updateUrl();
      elements.status.hidden = true;
      elements.content.hidden = false;
      const currentHash = window.location.hash;
      if (currentHash) {
        window.requestAnimationFrame(() => {
          try {
            const target = document.getElementById(decodeURIComponent(currentHash.slice(1)));
            if (!target) return;
            const previousBehavior = document.documentElement.style.scrollBehavior;
            document.documentElement.style.scrollBehavior = "auto";
            target.scrollIntoView();
            document.documentElement.style.scrollBehavior = previousBehavior;
          } catch {
            // Ignore malformed fragments; the explorer itself is still usable.
          }
        });
      }
    } catch (error) {
      showError(error);
    }
  }

  initialize();
})();
