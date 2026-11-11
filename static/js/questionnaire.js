(() => {
  const form = document.querySelector(".questionnaire-form");
  if (!form) return;

  const scrollToFirstInvalid = () => {
    if (form.checkValidity()) return false;

    const firstInvalid = form.querySelector(":invalid");
    if (!firstInvalid) return true;
    const target = firstInvalid.closest(".question-field, .consent-field") || firstInvalid;
    window.requestAnimationFrame(() => {
      firstInvalid.focus({ preventScroll: true });
      target.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "center",
      });
    });
    return true;
  };

  form.addEventListener("submit", (event) => {
    if (scrollToFirstInvalid()) event.preventDefault();
  });

  if (form.querySelector(".form-error, .form-alert")) scrollToFirstInvalid();
})();
