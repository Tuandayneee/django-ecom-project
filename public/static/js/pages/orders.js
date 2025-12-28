function filterOrders(status) {
  document
    .querySelectorAll(".nav-link")
    .forEach((el) => el.classList.remove("active"));
  event.target.classList.add("active");

  const items = document.querySelectorAll(".order-item-wrapper");
  let hasVisible = false;

  items.forEach((item) => {
    if (status === "all" || item.dataset.status === status) {
      item.style.display = "block";
      hasVisible = true;
    } else {
      item.style.display = "none";
    }
  });
}
