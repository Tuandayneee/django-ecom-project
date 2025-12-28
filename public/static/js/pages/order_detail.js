document.addEventListener("DOMContentLoaded", function () {
  var reviewModal = document.getElementById("reviewModal");

  reviewModal.addEventListener("show.bs.modal", function (event) {
    // 1. Nút đã bấm
    var button = event.relatedTarget;

    // 2. Lấy dữ liệu từ data attributes
    var productName = button.getAttribute("data-product-name");
    var productImg = button.getAttribute("data-product-img");
    var submitUrl = button.getAttribute("data-url");

    // 3. Điền vào Modal
    var modalTitle = reviewModal.querySelector("#modalProductName");
    var modalImg = reviewModal.querySelector("#modalProductImg");
    var modalForm = reviewModal.querySelector("#reviewForm");

    modalTitle.textContent = productName;
    modalImg.src = productImg;

    // 4. Cập nhật action của form
    modalForm.action = submitUrl;
  });
});
