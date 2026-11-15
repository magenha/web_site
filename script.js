document.documentElement.classList.add("js");

const navToggle = document.querySelector(".nav-toggle");
const siteNavigation = document.querySelector(".site-nav");

function closeNavigation() {
  if (!navToggle || !siteNavigation) return;
  navToggle.setAttribute("aria-expanded", "false");
  siteNavigation.classList.remove("is-open");
  document.body.classList.remove("nav-open");
  const label = navToggle.querySelector(".sr-only");
  if (label) label.textContent = navToggle.dataset.labelOpen || "Open navigation";
}

if (navToggle && siteNavigation) {
  navToggle.addEventListener("click", () => {
    const isOpen = navToggle.getAttribute("aria-expanded") === "true";
    navToggle.setAttribute("aria-expanded", String(!isOpen));
    siteNavigation.classList.toggle("is-open", !isOpen);
    document.body.classList.toggle("nav-open", !isOpen);
    const label = navToggle.querySelector(".sr-only");
    if (label) {
      label.textContent = isOpen
        ? (navToggle.dataset.labelOpen || "Open navigation")
        : (navToggle.dataset.labelClose || "Close navigation");
    }
  });

  siteNavigation.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeNavigation);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeNavigation();
  });

  const desktopNavigation = window.matchMedia("(min-width: 1201px)");
  const handleDesktopNavigation = (event) => {
    if (event.matches) closeNavigation();
  };

  if (desktopNavigation.addEventListener) {
    desktopNavigation.addEventListener("change", handleDesktopNavigation);
  } else {
    desktopNavigation.addListener(handleDesktopNavigation);
  }
}

document.querySelectorAll("a[hreflang]").forEach((link) => {
  link.addEventListener("click", () => {
    if (!window.location.hash) return;
    const target = new URL(link.href);
    target.hash = window.location.hash;
    link.href = target.toString();
  });
});

document.querySelectorAll("[data-current-year]").forEach((year) => {
  year.textContent = String(new Date().getFullYear());
});

const revealItems = [...document.querySelectorAll(".reveal")];
const calmMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if ("IntersectionObserver" in window && !calmMotion) {
  let revealObserverAlive = false;
  const revealObserver = new IntersectionObserver((entries, observer) => {
    revealObserverAlive = true;
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      entry.target.classList.remove("reveal--pending");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8%", threshold: 0.08 });

  revealItems.forEach((item) => {
    // What is already on screen (or above it) is shown at once, so nothing blinks; the rest waits for its entrance.
    if (item.getBoundingClientRect().top < window.innerHeight * 0.92) {
      item.classList.add("is-visible");
      return;
    }
    item.classList.add("reveal--pending");
    revealObserver.observe(item);
  });
  // Safety net: an observer always reports at once; if it stays silent (some renderers), show everything.
  setTimeout(() => {
    if (revealObserverAlive) return;
    revealItems.forEach((item) => { item.classList.remove("reveal--pending"); item.classList.add("is-visible"); });
  }, 1500);
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const pageIndex = document.querySelector(".page-index");
const indexLinks = pageIndex ? [...pageIndex.querySelectorAll("nav a")] : [];
const indexedSections = indexLinks
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

// On narrow screens the side index becomes a sticky «On this page» bar: it names the current section and opens the list.
// The button is hidden on wide screens by CSS; without JavaScript the plain list is shown.
let indexCurrent = null;
if (pageIndex && indexLinks.length) {
  const indexNav = pageIndex.querySelector("nav");
  const indexHeading = pageIndex.querySelector(":scope > p");
  indexNav.id = indexNav.id || "page-index-links";
  const indexToggle = document.createElement("button");
  indexToggle.type = "button";
  indexToggle.className = "page-index__toggle";
  indexToggle.setAttribute("aria-expanded", "false");
  indexToggle.setAttribute("aria-controls", indexNav.id);
  const indexLabel = document.createElement("span");
  indexLabel.className = "page-index__label";
  indexLabel.textContent = indexHeading ? indexHeading.textContent.trim() : "";
  indexCurrent = document.createElement("span");
  indexCurrent.className = "page-index__current";
  indexCurrent.textContent = indexLinks[0].textContent.trim();
  indexToggle.append(indexLabel, indexCurrent);
  pageIndex.insertBefore(indexToggle, indexNav);

  const setIndexOpen = (open) => {
    pageIndex.classList.toggle("is-open", open);
    indexToggle.setAttribute("aria-expanded", String(open));
  };
  indexToggle.addEventListener("click", () => setIndexOpen(!pageIndex.classList.contains("is-open")));
  indexLinks.forEach((link) => link.addEventListener("click", () => setIndexOpen(false)));
  document.addEventListener("click", (event) => {
    if (!pageIndex.contains(event.target)) setIndexOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !pageIndex.classList.contains("is-open")) return;
    setIndexOpen(false);
    indexToggle.focus();
  });
}

// The current section is the last one whose top has passed a line 30% down the screen (reliable with long sections).
if (indexedSections.length) {
  let activeSection = null;
  const updateActiveSection = () => {
    const line = window.innerHeight * 0.3;
    let current = indexedSections[0];
    indexedSections.forEach((section) => {
      if (section.getBoundingClientRect().top <= line) current = section;
    });
    if (current === activeSection) return;
    activeSection = current;
    indexLinks.forEach((link) => link.removeAttribute("aria-current"));
    const activeLink = indexLinks.find((link) => link.getAttribute("href") === `#${current.id}`);
    if (!activeLink) return;
    activeLink.setAttribute("aria-current", "location");
    if (indexCurrent) indexCurrent.textContent = activeLink.textContent.trim();
  };
  let indexFrame = 0;
  window.addEventListener("scroll", () => {
    if (!indexFrame) indexFrame = requestAnimationFrame(() => { indexFrame = 0; updateActiveSection(); });
  }, { passive: true });
  window.addEventListener("resize", updateActiveSection);
  updateActiveSection();
}

// DNA program: the two direct lines. A button focuses its line (and redraws it); pressing it again shows both.
document.querySelectorAll("[data-lineage-explainer]").forEach((box) => {
  const buttons = [...box.querySelectorAll("[data-line]")];
  const texts = [...box.querySelectorAll("[data-line-text]")];
  const show = (line) => {
    box.dataset.active = line;
    buttons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.line === line)));
    texts.forEach((text) => { text.hidden = text.dataset.lineText !== line; });
  };
  buttons.forEach((button) => button.addEventListener("click", () => {
    show(box.dataset.active === button.dataset.line ? "both" : button.dataset.line);
  }));
});

// Accessible tabs ([data-tabs]): click or arrow keys. Without JavaScript every panel is shown one after another.
document.querySelectorAll("[data-tabs]").forEach((box) => {
  const tabs = [...box.querySelectorAll('[role="tab"]')];
  const panels = tabs.map((tab) => document.getElementById(tab.getAttribute("aria-controls")));
  const select = (index, focus) => {
    tabs.forEach((tab, i) => {
      tab.setAttribute("aria-selected", String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      if (panels[i]) panels[i].hidden = i !== index;
    });
    if (focus) tabs[index].focus();
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(i));
    tab.addEventListener("keydown", (event) => {
      const moves = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 };
      if (!(event.key in moves)) return;
      event.preventDefault();
      select((moves[event.key] + tabs.length) % tabs.length, true);
    });
  });
  box.classList.add("is-tabbed");
  select(0);
});

const inquiryForm = document.querySelector("[data-inquiry-form]");

if (inquiryForm) {
  const isSpanish = inquiryForm.dataset.language === "es";
  const copyButton = inquiryForm.querySelector("[data-copy-inquiry]");
  const statusMessage = inquiryForm.querySelector("[data-form-status]");
  const copyPanel = inquiryForm.querySelector("[data-copy-panel]");
  const copyOutput = inquiryForm.querySelector("[data-copy-output]");
  const recipient = "contactmagenha@gmail.com";

  const language = isSpanish ? {
    subject: "Consulta desde el sitio web de MAGENHA",
    heading: "CONSULTA DESDE EL SITIO WEB DE MAGENHA",
    languageLabel: "Idioma",
    languageValue: "Español",
    name: "Nombre completo",
    email: "Correo de respuesta",
    clientStatus: "Situación como cliente",
    requestType: "Tipo de consulta",
    places: "Lugares pertinentes",
    period: "Período aproximado",
    goal: "Objetivo y datos conocidos",
    sources: "Fuentes ya consultadas",
    sourcePage: "Página de origen",
    notProvided: "No indicado",
    draftOpened: "Su aplicación de correo debería abrirse ahora. Todavía no se ha enviado nada: revise el borrador y pulse Enviar.",
    copied: "La consulta se ha copiado. Péguela en un mensaje dirigido a contactmagenha@gmail.com.",
    copyFallback: "No se pudo copiar automáticamente. Seleccione el texto mostrado y cópielo para pegarlo en su correo.",
    tooLong: "La consulta es demasiado extensa para abrir un borrador de forma fiable. Copie el texto mostrado y péguelo en un mensaje dirigido a contactmagenha@gmail.com."
  } : {
    subject: "MAGENHA website inquiry",
    heading: "MAGENHA WEBSITE INQUIRY",
    languageLabel: "Language",
    languageValue: "English",
    name: "Full name",
    email: "Reply email",
    clientStatus: "Client status",
    requestType: "Request type",
    places: "Relevant place(s)",
    period: "Approximate period",
    goal: "Research goal and known facts",
    sources: "Sources already consulted",
    sourcePage: "Source page",
    notProvided: "Not provided",
    draftOpened: "Your email application should now open. Nothing has been sent yet: review the draft and press Send.",
    copied: "The inquiry has been copied. Paste it into a message addressed to contactmagenha@gmail.com.",
    copyFallback: "Automatic copying was unavailable. Select the text shown and copy it into your email.",
    tooLong: "This inquiry is too long to open reliably as an email draft. Copy the text shown and paste it into a message addressed to contactmagenha@gmail.com."
  };

  const getValue = (name) => {
    const control = inquiryForm.elements.namedItem(name);
    return control ? control.value.trim() : "";
  };

  const getSelectedText = (name) => {
    const control = inquiryForm.elements.namedItem(name);
    if (!control || typeof control.selectedIndex !== "number") return "";
    const option = control.options[control.selectedIndex];
    return option ? option.textContent.trim() : "";
  };

  const serviceFields = () => inquiryForm.dataset.service === "spain" ? [
    `${isSpanish ? "Servicio" : "Service"}: MAGENHA Research — ${isSpanish ? "España" : "Spain"}`,
    `${isSpanish ? "País de residencia" : "Country of residence"}: ${getValue("country")}`,
    `${isSpanish ? "Finalidad" : "Purpose"}: ${getSelectedText("purpose")}`
  ] : [];

  const buildInquiry = () => [
    language.heading,
    ...serviceFields(),
    "",
    `${language.languageLabel}: ${language.languageValue}`,
    `${language.name}: ${getValue("name")}`,
    `${language.email}: ${getValue("email")}`,
    `${language.clientStatus}: ${getSelectedText("client_status")}`,
    `${language.requestType}: ${getSelectedText("request_type")}`,
    `${language.places}: ${getValue("places")}`,
    `${language.period}: ${getValue("period") || language.notProvided}`,
    "",
    `${language.goal}:`,
    getValue("goal"),
    "",
    `${language.sources}:`,
    getValue("sources") || language.notProvided,
    "",
    `${language.sourcePage}: ${window.location.href.split("#")[0]}`
  ].join("\r\n");

  const showCopyText = (body) => {
    if (!copyPanel || !copyOutput) return;
    copyOutput.value = body;
    copyPanel.hidden = false;
  };

  const setStatus = (message, success = false) => {
    if (!statusMessage) return;
    statusMessage.textContent = message;
    statusMessage.dataset.state = success ? "success" : "notice";
  };

  inquiryForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!inquiryForm.reportValidity()) return;

    const body = buildInquiry();
    const mailto = `mailto:${recipient}?subject=${encodeURIComponent(language.subject)}&body=${encodeURIComponent(body)}`;
    showCopyText(body);

    if (mailto.length > 1900) {
      setStatus(language.tooLong);
      copyOutput?.focus();
      copyOutput?.select();
      return;
    }

    setStatus(language.draftOpened, true);
    window.location.href = mailto;
  });

  copyButton?.addEventListener("click", async () => {
    if (!inquiryForm.reportValidity()) return;

    const body = buildInquiry();
    showCopyText(body);

    try {
      await navigator.clipboard.writeText(body);
      setStatus(language.copied, true);
    } catch {
      setStatus(language.copyFallback);
      copyOutput?.focus();
      copyOutput?.select();
    }
  });
}
