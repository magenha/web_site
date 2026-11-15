/* Genealogy in Cuba: star ratings from the public JSON, and the researcher-suggestion form link. */
(() => {
  // The Google Forms link for suggesting researchers (one place for both languages). After changing it, change
  // "cuba.js?v=…" in cuba.html and es/cuba.html. If it is empty the button stays hidden and an "available soon" note shows.
  const SUGGEST_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScU7KNUAJjjg-7YLSh8cqpxVzErE-y85svE0p9ZIXLVGLYwCw/viewform";

  const es = document.documentElement.lang === "es";
  const T = es ? {
    locale: "es-ES",
    none: "Sin valoraciones todavía",
    unavailable: "Las valoraciones no están disponibles en este momento.",
    average: "Valoración media:",
    count: n => (n === 1 ? "1 valoración" : `${n.toLocaleString("es-ES")} valoraciones`)
  } : {
    locale: "en-GB",
    none: "No ratings yet",
    unavailable: "Ratings are not available right now.",
    average: "Average rating:",
    count: n => (n === 1 ? "1 rating" : `${n.toLocaleString("en-GB")} ratings`)
  };

  const suggestLink = document.querySelector("[data-suggest-form]");
  const suggestPending = document.querySelector("[data-suggest-pending]");
  if (suggestLink && /^https:\/\//.test(SUGGEST_FORM_URL)) {
    suggestLink.href = SUGGEST_FORM_URL;
    suggestLink.hidden = false;
    if (suggestPending) suggestPending.hidden = true;
  }

  const list = document.querySelector("[data-ratings-url]");
  if (!list) return;
  const cards = [...list.querySelectorAll("[data-researcher]")];

  // state: "ok" (entry with ratings), "none" (no ratings yet) or "unavailable" (file or entry unusable).
  const show = (card, entry, failed) => {
    const box = card.querySelector("[data-rating]");
    const text = card.querySelector("[data-rating-text]");
    const fill = card.querySelector(".rating__fill");
    if (!box || !text || !fill) return;

    const count = entry && Number.isInteger(entry.rating_count) ? entry.rating_count : 0;
    const average = entry && typeof entry.average_rating === "number" ? entry.average_rating : null;
    let state = "ok";
    if (failed) state = "unavailable";
    else if (count < 1) state = "none";
    else if (average === null || average < 1 || average > 5) state = "unavailable";   // never shown as 0/5

    box.classList.toggle("rating--empty", state === "none");
    box.classList.toggle("rating--unavailable", state === "unavailable");
    text.textContent = "";
    if (state !== "ok") {
      fill.style.width = "0";
      text.textContent = state === "none" ? T.none : T.unavailable;
      return;
    }
    const rounded = Math.round(average * 10) / 10;
    fill.style.width = `${(rounded / 5) * 100}%`;
    const label = document.createElement("span");
    label.className = "sr-only";
    label.textContent = `${T.average} `;
    const shown = rounded.toLocaleString(T.locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    text.append(label, `${shown}/5 — ${T.count(count)}`);
  };

  fetch(list.dataset.ratingsUrl, { cache: "no-cache" })
    .then(response => {
      if (!response.ok) throw new Error("Ratings unavailable");
      return response.json();
    })
    .then(data => {
      if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Unexpected ratings file");
      cards.forEach(card => {
        const id = card.dataset.researcher;
        show(card, Object.prototype.hasOwnProperty.call(data, id) ? data[id] : null, false);
      });
    })
    .catch(() => cards.forEach(card => show(card, null, true)));
})();
