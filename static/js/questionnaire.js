(() => {
  const form = document.querySelector(".questionnaire-form");
  if (!form) return;

  let firstInvalid = null;
  form.addEventListener(
    "invalid",
    (event) => {
      if (firstInvalid) return;
      firstInvalid = event.target;
      window.requestAnimationFrame(() => {
        firstInvalid.focus({ preventScroll: true });
        firstInvalid.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth",
          block: "center",
        });
      });
    },
    true,
  );

  form.addEventListener("submit", () => {
    firstInvalid = null;
  });
})();
