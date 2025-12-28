document.getElementById("avatar-input").addEventListener("change", function () {
  if (this.files && this.files[0]) {
    document.getElementById("avatarLoading").style.display = "flex";

    setTimeout(() => {
      document.getElementById("avatar-form").submit();
    }, 500);
  }
});
