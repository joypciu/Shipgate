const sample = document.getElementById("sample-diff");
const button = document.getElementById("sample");
const field = document.querySelector("textarea[name=diff]");
if (sample && button && field) {
  button.addEventListener("click", () => {
    field.value = JSON.parse(sample.textContent || '""');
    field.focus();
  });
}
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    const submit = form.querySelector("button[type=submit]");
    if (!submit) return;
    window.setTimeout(() => {
      submit.disabled = true;
      submit.textContent = "Reviewing…";
    }, 0);
  });
});
