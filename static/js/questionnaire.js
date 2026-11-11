(() => {
  const form = document.querySelector(".questionnaire-form");
  if (!form) return;

  const clearInvalidState = (target) => {
    target.classList.remove("is-invalid-focus");
    target.nextElementSibling?.classList.contains("client-invalid-message") &&
      target.nextElementSibling.remove();
  };

  const markInvalidState = (target) => {
    target.classList.add("is-invalid-focus");
    if (target.nextElementSibling?.classList.contains("client-invalid-message")) return;

    const notice = document.createElement("p");
    notice.className = "client-invalid-message";
    notice.setAttribute("role", "alert");
    notice.textContent = target.classList.contains("scale-field")
      ? "Escolha uma nota de 1 a 5 para continuar."
      : "Confirme este item para continuar.";
    target.insertAdjacentElement("afterend", notice);
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

  form.addEventListener("input", () => {
    if (form.checkValidity()) {
      form.querySelectorAll(".is-invalid-focus").forEach(clearInvalidState);
    }
  });
  form.addEventListener("change", () => {
    if (form.checkValidity()) {
      form.querySelectorAll(".is-invalid-focus").forEach(clearInvalidState);
    }
  });

  if (form.querySelector(".form-error, .form-alert")) scrollToFirstInvalid();
})();
