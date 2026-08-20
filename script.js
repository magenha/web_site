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

const revealItems = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8%", threshold: 0.08 });

  revealItems.forEach((item) => revealObserver.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const indexLinks = [...document.querySelectorAll(".page-index a")];
const indexedSections = indexLinks
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

if (indexLinks.length && "IntersectionObserver" in window) {
  const sectionObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

    if (!visible) return;
    indexLinks.forEach((link) => link.removeAttribute("aria-current"));
    const activeLink = indexLinks.find((link) => link.getAttribute("href") === `#${visible.target.id}`);
    if (activeLink) activeLink.setAttribute("aria-current", "location");
  }, { rootMargin: "-18% 0px -65%", threshold: [0, 0.2, 0.5] });

  indexedSections.forEach((section) => sectionObserver.observe(section));
}

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

  const buildInquiry = () => [
    language.heading,
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
