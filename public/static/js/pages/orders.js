function filterOrders(status) {
  document
    .querySelectorAll(".nav-link")
    .forEach((el) => el.classList.remove("active"));
  if (typeof event !== "undefined" && event && event.target) {
    event.target.classList.add("active");
  }

  const normalized = (status || "all").toLowerCase();
  const items = document.querySelectorAll(".order-item-wrapper");

  items.forEach((item) => {
    const itemStatus = (item.dataset.status || "").toLowerCase();
    if (normalized === "all" || itemStatus === normalized) {
      item.style.display = "block";
    } else {
      item.style.display = "none";
    }
  });
}
