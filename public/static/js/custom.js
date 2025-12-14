/* static/js/custom.js */

/**
 * 1. Hàm định dạng tiền tệ Việt Nam (VNĐ)
 * Đầu vào: 150000 -> Đầu ra: "150.000 đ"
 */
function formatVND(amount) {
  if (isNaN(amount)) return "0 đ";
  return Number(amount).toLocaleString("vi-VN") + " đ";
}

/**
 * 2. Hàm đổi ảnh Gallery (Dùng cho trang Product Detail)
 * Yêu cầu: Ảnh chính có id="mainImage", Ảnh nhỏ có class="thumbnail-item"
 */
function changeImage(element, src) {
  const mainImage = document.getElementById("mainImage");
  if (mainImage) {
    // Hiệu ứng mờ nhẹ khi đổi ảnh cho mượt
    mainImage.style.opacity = "0";
    setTimeout(() => {
      mainImage.src = src;
      mainImage.style.opacity = "1";
    }, 150);

    // Xử lý active border
    document.querySelectorAll(".thumbnail-item").forEach((el) => {
      el.classList.remove("active-thumb");
    });
    element.classList.add("active-thumb");
  }
}

/**
 * 3. Hàm hiển thị thông báo Toast (Nếu bạn dùng Bootstrap Toast)
 * Ví dụ: showToast('Thêm giỏ hàng thành công', 'success')
 */
function showNotification(message, type = "success") {
  // Bạn có thể mở rộng sau này nếu muốn làm thông báo bay bay
  console.log(`[${type.toUpperCase()}] ${message}`);
  alert(message); // Tạm thời dùng alert, sau này thay bằng Toast đẹp hơn
}
