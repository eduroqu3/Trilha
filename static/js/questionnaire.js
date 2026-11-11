(() => {
  const form = document.querySelector(".questionnaire-form");
  if (!form) return;

  const clearInvalidState = (target) => {
    target.querySelectorAll(".client-invalid-message").forEach((notice) => notice.remove());
    target.nextElementSibling?.classList.contains("client-invalid-message") &&
      target.nextElementSibling.remove();
  };

  const markInvalidState = (target) => {
    if (target.querySelector(".client-invalid-message") ||
        target.nextElementSibling?.classList.contains("client-invalid-message")) return;

    const notice = document.createElement("p");
    notice.className = "client-invalid-message";
    notice.setAttribute("role", "alert");
    notice.textContent = target.classList.contains("scale-field")
      ? "Escolha uma nota de 1 a 5 para continuar."
      : "Confirme este item para continuar.";
    const anchor = target.classList.contains("scale-field")
      ? target.querySelector(".scale-options")
      : target.classList.contains("text-question")
        ? target.querySelector("textarea")
        : target;
    anchor.insertAdjacentElement("afterend", notice);
  };

  const clearValidTarget = (control) => {
    const target = control.closest(".question-field, .consent-field");
    if (!target) return;
    const controls = target.matches("input, textarea, select")
      ? [target]
      : [...target.querySelectorAll("input, textarea, select")];
    if (controls.every((field) => field.checkValidity())) clearInvalidState(target);
  };

  const scrollToFirstInvalid = () => {
    if (form.checkValidity()) return false;

    const firstInvalid = form.querySelector(":invalid");
    if (!firstInvalid) return true;
    const target = firstInvalid.closest(".question-field, .consent-field") || firstInvalid;
    markInvalidState(target);
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

  form.addEventListener("input", (event) => clearValidTarget(event.target));
  form.addEventListener("change", (event) => clearValidTarget(event.target));

  if (form.querySelector(".form-error, .form-alert")) scrollToFirstInvalid();
})();
