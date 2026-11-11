document.addEventListener("DOMContentLoaded", () => {
  const toasts = document.querySelectorAll(".custom-toast");

  toasts.forEach((toast, index) => {
    // Hiệu ứng xuất hiện so le (nếu có nhiều tin nhắn cùng lúc)
    setTimeout(() => {
      toast.classList.add("active");
      initToastLogic(toast);
    }, index * 200);
  });
});

function initToastLogic(toast) {
  const DURATION = 5000; // 5 giây
  const progressBar = toast.querySelector(".toast-progress-bar");

  let startTime = Date.now();
  let remaining = DURATION;
  let timerId;
  let isPaused = false;

  // Hàm cập nhật thanh Progress Bar
  const updateProgress = () => {
    if (isPaused) return;

    const elapsed = Date.now() - startTime;
    const percentage = Math.max(0, 100 - (elapsed / DURATION) * 100);

    if (progressBar) {
      progressBar.style.transform = `scaleX(${percentage / 100})`;
    }

    if (elapsed >= DURATION) {
      removeToast(toast);
    } else {
      timerId = requestAnimationFrame(updateProgress);
    }
  };

  // Bắt đầu chạy
  timerId = requestAnimationFrame(updateProgress);

  // --- PAUSE ON HOVER (Tính năng Senior) ---
  toast.addEventListener("mouseenter", () => {
    isPaused = true;
    cancelAnimationFrame(timerId);
    // Tính toán thời gian còn lại khi pause
    remaining -= Date.now() - startTime;
  });

  toast.addEventListener("mouseleave", () => {
    isPaused = false;
    // Reset start time để chạy tiếp phần remaining
    startTime = Date.now() - (DURATION - remaining);
    timerId = requestAnimationFrame(updateProgress);
  });
}

// Hàm xóa Toast
function removeToast(toast) {
  toast.classList.remove("active"); // Slide out
  toast.classList.add("closing");

  // Đợi animation CSS chạy xong (0.4s) rồi mới xóa khỏi DOM
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 400);
}
