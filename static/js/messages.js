(() => {
  const messages = document.querySelectorAll(".site-messages");
  messages.forEach((message) => {
    window.setTimeout(() => {
      message.classList.add("is-hidden");
      window.setTimeout(() => message.remove(), 350);
    }, 3500);
  });
})();
