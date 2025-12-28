// public/static/js/pages/address.js

document.addEventListener("DOMContentLoaded", function () {
  const API_URL = "https://provinces.open-api.vn/api/";

  const provinceSelect = document.getElementById("province");
  const districtSelect = document.getElementById("district");
  const wardSelect = document.getElementById("ward");

  const cityNameInput = document.getElementById("city_name");
  const districtNameInput = document.getElementById("district_name");
  const wardNameInput = document.getElementById("ward_name"); // Đảm bảo bạn có dòng này

  const callAPI = async (endpoint) => {
    try {
      const response = await axios.get(endpoint);
      return response.data;
    } catch (error) {
      console.error("Lỗi API địa chỉ:", error);
      return [];
    }
  };

  const renderOption = (array, selector, type) => {
    let row = `<option value="">-- Chọn ${type} --</option>`;
    array.forEach((element) => {
      row += `<option value="${element.code}" data-name="${element.name}">${element.name}</option>`;
    });
    document.querySelector(selector).innerHTML = row;
  };

  const loadProvinces = async () => {
    const data = await callAPI(API_URL + "?depth=1");
    renderOption(data, "#province", "Tỉnh/Thành");
  };
  loadProvinces();

  // 3. Sự kiện chọn Tỉnh -> Load Huyện
  if (provinceSelect) {
    provinceSelect.addEventListener("change", async function () {
      districtSelect.disabled = true;
      wardSelect.disabled = true;
      districtSelect.innerHTML = '<option value="">-- Đang tải... --</option>';
      wardSelect.innerHTML = '<option value="">-- Phường/Xã --</option>';

      const provinceCode = this.value;
      if (provinceCode) {
        const data = await callAPI(API_URL + "p/" + provinceCode + "?depth=2");
        renderOption(data.districts, "#district", "Quận/Huyện");
        districtSelect.disabled = false;

        const selectedOption = this.options[this.selectedIndex];
        if (cityNameInput)
          cityNameInput.value = selectedOption.getAttribute("data-name");
      } else {
        if (cityNameInput) cityNameInput.value = "";
      }
    });
  }

  // 4. Sự kiện chọn Huyện -> Load Xã
  if (districtSelect) {
    districtSelect.addEventListener("change", async function () {
      wardSelect.disabled = true;
      wardSelect.innerHTML = '<option value="">-- Đang tải... --</option>';

      const districtCode = this.value;
      if (districtCode) {
        const data = await callAPI(API_URL + "d/" + districtCode + "?depth=2");
        renderOption(data.wards, "#ward", "Phường/Xã");
        wardSelect.disabled = false;

        const selectedOption = this.options[this.selectedIndex];
        if (districtNameInput)
          districtNameInput.value = selectedOption.getAttribute("data-name");
      } else {
        if (districtNameInput) districtNameInput.value = "";
      }
    });
  }

  // 5. Sự kiện chọn Xã -> Lưu kết quả
  if (wardSelect) {
    wardSelect.addEventListener("change", function () {
      const wardCode = this.value;
      const selectedOption = this.options[this.selectedIndex];

      if (wardCode) {
        if (wardNameInput) {
          wardNameInput.value = selectedOption.getAttribute("data-name");
        }
        printResult();
      } else {
        if (wardNameInput) wardNameInput.value = "";
      }
    });
  }

  const printResult = () => {
    if (provinceSelect.value && districtSelect.value && wardSelect.value) {
      const p =
        provinceSelect.options[provinceSelect.selectedIndex].getAttribute(
          "data-name"
        );
      const d =
        districtSelect.options[districtSelect.selectedIndex].getAttribute(
          "data-name"
        );
      const w =
        wardSelect.options[wardSelect.selectedIndex].getAttribute("data-name");

      const resultString = `${w}, ${d}, ${p}`;
      console.log("Địa chỉ đầy đủ:", resultString);

      const resultInput = document.getElementById("result");
      if (resultInput) resultInput.value = resultString;
    }
  };
});
