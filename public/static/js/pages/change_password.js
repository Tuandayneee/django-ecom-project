document.addEventListener("DOMContentLoaded", function () {
  const inputs = document.querySelectorAll("input");
  inputs.forEach((input) => {
    input.classList.add("input-custom");
    input.classList.remove("form-control");
  });
});
