(() => {
  const list = document.querySelector("[data-question-list]");
  if (!list) return;

  const status = document.querySelector("[data-editor-status]");
  const showStatus = (text, kind = "success") => {
    if (!status) return;
    status.textContent = text;
    status.className = `ajax-status ajax-status-${kind}`;
    status.hidden = false;
  };

  const updateNumbers = () => {
    list.querySelectorAll("[data-question-item]").forEach((item, index) => {
      const number = item.querySelector("[data-question-number]");
      if (number) number.textContent = `${index + 1}.`;
      item.querySelector('[data-mover="subir"]').disabled = index === 0;
      item.querySelector('[data-mover="descer"]').disabled = index === list.children.length - 1;
    });
  };

  list.querySelectorAll("[data-ajax-order]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitter = event.submitter;
      if (!submitter || submitter.disabled) return;
      const buttons = form.querySelectorAll("button");
      buttons.forEach((button) => { button.disabled = true; });
      try {
        const response = await fetch(form.action || window.location.href, {
          method: "POST",
          body: new FormData(form),
          headers: { "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin",
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.message || "Não foi possível reordenar a pergunta.");
        const items = new Map([...list.querySelectorAll("[data-question-item]")].map((item) => [item.dataset.questionId, item]));
        data.ordens.forEach(({ id }) => {
          const item = items.get(String(id));
          if (item) list.appendChild(item);
        });
        updateNumbers();
        showStatus(data.message);
      } catch (error) {
        showStatus(error.message, "error");
        buttons.forEach((button) => { button.disabled = false; });
      }
    });
  });

  updateNumbers();
})();
