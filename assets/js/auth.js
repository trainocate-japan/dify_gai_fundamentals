(function () {
  const key = "auth_ok";
  const pass = "t_ws_doc";
  const root = document.documentElement;

  if (sessionStorage.getItem(key) === "1") {
    return;
  }

  root.style.display = "none";
  const input = window.prompt("Password:");
  if (input === pass) {
    sessionStorage.setItem(key, "1");
    root.style.display = "";
  }
})();
