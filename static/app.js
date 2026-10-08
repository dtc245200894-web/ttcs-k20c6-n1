const authView = document.querySelector("#authView");
const registrationView = document.querySelector("#registrationView");
const passwordResetView = document.querySelector("#passwordResetView");
const dashboardView = document.querySelector("#dashboardView");
const accountMenu = document.querySelector("#accountMenu");
const accountMenuTrigger = document.querySelector("#accountMenuTrigger");
const accountMenuDropdown = document.querySelector("#accountMenuDropdown");
const dashboardAvatarMenu = document.querySelector("#dashboardAvatarMenu");
const dashboardAvatarButton = document.querySelector("#dashboardAvatarButton");
const dashboardAvatarActions = document.querySelector("#dashboardAvatarActions");
const logoutButton = document.querySelector("#logoutButton");
const profileModal = document.querySelector("#profileModal");
const avatarViewModal = document.querySelector("#avatarViewModal");
const rentalDetailsModal = document.querySelector("#rentalDetailsModal");
const rentalDetailsList = document.querySelector("#rentalDetailsList");
const checkoutCurrentRentalButton = document.querySelector("#checkoutCurrentRental");
const rentalCheckoutMessage = document.querySelector("#rentalCheckoutMessage");
const checkoutConfirmModal = document.querySelector("#checkoutConfirmModal");
const checkoutConfirmMessage = document.querySelector("#checkoutConfirmMessage");
const cancelCheckoutButton = document.querySelector("#cancelCheckout");
const confirmCheckoutButton = document.querySelector("#confirmCheckout");
const rentalTransferPanel = document.querySelector("#rentalTransferPanel");
const transferRoomSearch = document.querySelector("#transferRoomSearch");
const transferRoomResults = document.querySelector("#transferRoomResults");
const transferRoomSelected = document.querySelector("#transferRoomSelected");
const rentalTransferDropzone = document.querySelector("#rentalTransferDropzone");
const rentalTransferMessage = document.querySelector("#rentalTransferMessage");
const avatarViewImage = document.querySelector("#avatarViewImage");
const avatarViewPlaceholder = document.querySelector("#avatarViewPlaceholder");
const profileForm = document.querySelector("#profileForm");
const profileFormMessage = document.querySelector("#profileFormMessage");
const profileAvatarInput = document.querySelector("#profileAvatar");
const profileAvatarPreview = document.querySelector("#profileAvatarPreview");
const profileAvatarPlaceholder = document.querySelector("#profileAvatarPlaceholder");
const saveProfileButton = document.querySelector("#saveProfileButton");
let currentUser = null;
let rentalDetailsRoomId = null;
let transferTargetRoomId = null;
const loginForm = document.querySelector("#loginForm");
const registrationForm = document.querySelector("#registrationForm");
const formMessage = document.querySelector("#formMessage");
const formMessageText = document.querySelector("#formMessageText");
const forgotPasswordLink = document.querySelector("#forgotPasswordLink");
const registrationMessage = document.querySelector("#registrationMessage");
const passwordResetRequestForm = document.querySelector("#passwordResetRequestForm");
const passwordResetCompleteForm = document.querySelector("#passwordResetCompleteForm");
const passwordResetRequestMessage = document.querySelector("#passwordResetRequestMessage");
const passwordResetCompleteMessage = document.querySelector("#passwordResetCompleteMessage");
const roomsGrid = document.querySelector("#roomsGrid");
const overviewRoomsGrid = document.querySelector("#overviewRoomsGrid");
const rentalHistorySearch = document.querySelector("#rentalHistorySearch");
let rentalHistoryRentals = [];
let rentalHistoryError = "";
const roomForm = document.querySelector("#roomForm");
const roomFormPanel = document.querySelector("#roomFormPanel");
const roomFormModal = document.querySelector("#roomFormModal");
const rentalFormModal = document.querySelector("#rentalFormModal");
const rentalForm = document.querySelector("#rentalForm");
const rentalCustomerName = document.querySelector("#rentalCustomerName");
const rentalCustomerPhone = document.querySelector("#rentalCustomerPhone");
const rentalRoomInput = document.querySelector("#rentalRoom");
const rentalRoomIdInput = document.querySelector("#rentalRoomId");
const rentalRoomResults = document.querySelector("#rentalRoomResults");
const rentalRoomDetails = document.querySelector("#rentalRoomDetails");
const rentalStartDateInput = document.querySelector("#rentalStartDate");
const rentalStartTimeInput = document.querySelector("#rentalStartTime");
const rentalEndInput = document.querySelector("#rentalEnd");
const rentalCheckoutTime = document.querySelector("#rentalCheckoutTime");
const rentalDuration = document.querySelector("#rentalDuration");
const rentalTotal = document.querySelector("#rentalTotal");
const rentalFormMessage = document.querySelector("#rentalFormMessage");
const roomImageInput = document.querySelector("#roomImage");
const roomImageUrlInput = document.querySelector("#roomImageUrl");
const roomImageName = document.querySelector("#roomImageName");
const addRoomTypeModal = document.querySelector("#addRoomTypeModal");
const moveRoomTypeModal = document.querySelector("#moveRoomTypeModal");
const deleteConfirmModal = document.querySelector("#deleteConfirmModal");
const moveRoomTypeConfirmModal = document.querySelector("#moveRoomTypeConfirmModal");
const deleteConfirmTitle = document.querySelector("#deleteConfirmTitle");
const deleteConfirmKicker = document.querySelector("#deleteConfirmModal .kicker");
const deleteConfirmMessage = document.querySelector("#deleteConfirmMessage");
const cancelDeleteButton = document.querySelector("#cancelDelete");
const confirmDeleteButton = document.querySelector("#confirmDelete");
const cancelMoveRoomTypeConfirmButton = document.querySelector("#cancelMoveRoomTypeConfirm");
const confirmMoveRoomTypeButton = document.querySelector("#confirmMoveRoomType");
const moveRoomTypeConfirmMessage = document.querySelector("#moveRoomTypeConfirmMessage");
const roomTypePickerControl = document.querySelector("#roomTypePickerControl");
const roomTypePickerTrigger = document.querySelector("#roomTypePickerTrigger");
const roomTypePickerValue = document.querySelector("#roomTypePickerValue");
const roomTypeList = document.querySelector("#roomTypeList");
document.body.append(roomFormModal, rentalFormModal, addRoomTypeModal, moveRoomTypeModal, deleteConfirmModal, moveRoomTypeConfirmModal, profileModal, avatarViewModal, rentalDetailsModal);
const roomFormTitle = document.querySelector("#roomFormTitle");
const roomFormMessage = document.querySelector("#roomFormMessage");
const roomTypeFormMessage = document.querySelector("#roomTypeFormMessage");
const moveRoomTypeFormMessage = document.querySelector("#moveRoomTypeFormMessage");
const successToast = document.querySelector("#successToast");
const successToastMessage = document.querySelector("#successToastMessage");
let successToastTimer;

const roomStatusMap = {
  available: "Trống",
  occupied: "Đã thuê",
  cleaning: "Đang dọn",
  maintenance: "Bảo trì",
};

let roomTypeMap = {
  single: "Single",
  double: "Double",
  vip: "VIP",
};

let currentFilter = "all";
let selectedRoomType = null;
let pendingDeleteRoomId = null;
let pendingDeleteRoomTypeSlug = null;
let pendingDeleteRentalId = null;
let deleteTrigger = null;
let pendingRoomTypeTransfer = null;

function setDashboardView(view) {
  document.querySelectorAll(".nav-button[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll("[data-dashboard-view]").forEach((section) => {
    section.classList.toggle("active", section.dataset.dashboardView === view);
  });
  const viewLabels = {
    rooms: "QUẢN LÝ PHÒNG",
    "room-types": "THỂ LOẠI PHÒNG",
    history: "LỊCH SỬ",
  };
  document.querySelector(".dashboard-header .kicker").textContent = `LOTUS STAY / ${viewLabels[view] || "TRANG CHỦ"}`;
  fitRoomTypeResults();
  if (view === "history") loadRentalHistory();
}

function fitRoomTypeResults() {
  const section = document.querySelector("[data-dashboard-view='room-types']");
  const grid = document.querySelector("#typeRoomsGrid");
  if (!section.classList.contains("active")) return;
  const sidebarBottom = document.querySelector(".sidebar-panel").getBoundingClientRect().bottom;
  const gridTop = grid.getBoundingClientRect().top;
  if (gridTop >= sidebarBottom) {
    grid.style.maxHeight = "";
    return;
  }
  grid.style.maxHeight = `${Math.max(0, Math.floor(sidebarBottom - gridTop))}px`;
}

function renderRoomTypes() {
  const rooms = window.__roomList || [];
  roomTypeList.innerHTML = Object.entries(roomTypeMap).map(([type, label]) => {
    const count = rooms.filter((room) => room.room_type === type).length;
    return `
      <div class="room-type-row">
        <button class="room-type-select" type="button" data-action="select" data-room-type="${escapeHtml(type)}" aria-pressed="${selectedRoomType === type}">
          <span>${escapeHtml(label)}</span>
          <small>${count} phòng</small>
        </button>
        <button class="mini-button danger room-type-delete" type="button" data-action="delete" data-room-type="${escapeHtml(type)}" aria-label="Xóa thể loại ${escapeHtml(label)}" title="Xóa thể loại">Xóa</button>
      </div>
    `;
  }).join("");
  if (!Object.keys(roomTypeMap).length) {
    roomTypeList.innerHTML = '<p class="move-room-type-empty">Chưa có thể loại phòng.</p>';
  }
  roomTypePickerValue.textContent = selectedRoomType ? roomTypeMap[selectedRoomType] : "Chọn thể loại phòng";
  renderTypeRooms();
  fitRoomTypeResults();
}

function closeRoomTypePicker() {
  roomTypeList.classList.add("hidden");
  roomTypePickerTrigger.setAttribute("aria-expanded", "false");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function renderTypeRooms() {
  const title = document.querySelector("#typeRoomsTitle");
  const grid = document.querySelector("#typeRoomsGrid");
  if (!selectedRoomType) {
    title.textContent = "Phòng theo thể loại";
    grid.innerHTML = '<p class="type-rooms-empty">Chọn một thể loại để xem danh sách phòng.</p>';
    return;
  }

  const rooms = (window.__roomList || []).filter((room) => room.room_type === selectedRoomType);
  title.textContent = `Phòng ${roomTypeMap[selectedRoomType]}`;
  if (!rooms.length) {
    grid.innerHTML = '<p class="type-rooms-empty">Chưa có phòng thuộc thể loại này.</p>';
    return;
  }

  grid.innerHTML = rooms.map((room) => `
    <article class="type-room-card">
      <img src="${escapeHtml(room.image_url || "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80")}" alt="${escapeHtml(room.name)}">
      <div class="type-room-details">
        <div class="type-room-heading">
          <strong>${escapeHtml(room.code)}</strong>
          <span class="room-status status-${escapeHtml(room.status)}">${escapeHtml(roomStatusMap[room.status] || room.status)}</span>
        </div>
        <h5>${escapeHtml(room.name)}</h5>
        <p>${escapeHtml(room.description || "Khách sạn Lotus Stay.")}</p>
        <div class="type-room-footer"><span>Tầng ${escapeHtml(room.floor)}</span><strong>${formatCurrency(room.price)}</strong></div>
      </div>
    </article>
  `).join("");
}

function renderMoveRoomChoices() {
  const list = document.querySelector("#moveRoomTypeRoomList");
  const sourceSlug = document.querySelector("#sourceRoomType").value;
  if (!sourceSlug) {
    list.innerHTML = '<p class="move-room-type-empty">Chọn thể loại hiện tại để xem danh sách phòng.</p>';
    return;
  }

  const rooms = (window.__roomList || []).filter((room) => room.room_type === sourceSlug);
  if (!rooms.length) {
    list.innerHTML = '<p class="move-room-type-empty">Thể loại này chưa có phòng.</p>';
    return;
  }

  list.innerHTML = rooms.map((room) => `
    <label class="move-room-type-room-option">
      <input type="checkbox" name="room_ids" value="${escapeHtml(room.id)}">
      <span>
        <strong>${escapeHtml(room.name)}</strong>
        <small>${escapeHtml(room.code)} · Tầng ${escapeHtml(room.floor)}</small>
      </span>
    </label>
  `).join("");
}

async function loadRoomTypes() {
  try {
    const response = await fetch("/api/room-types");
    const result = await response.json();
    if (!response.ok) {
      roomTypeFormMessage.textContent = result.message || "Không thể tải thể loại phòng.";
      return;
    }

    const roomTypes = result.room_types || [];
    roomTypeMap = Object.fromEntries(roomTypes.map((roomType) => [roomType.slug, roomType.name]));
    if (!roomTypeMap[selectedRoomType]) selectedRoomType = null;
    const sourceRoomType = document.querySelector("#sourceRoomType");
    const targetRoomType = document.querySelector("#targetRoomType");
    const previousSource = sourceRoomType.value;
    const previousTarget = targetRoomType.value;
    sourceRoomType.replaceChildren(new Option("Chọn thể loại cần chuyển", ""), ...roomTypes.map((roomType) => new Option(roomType.name, roomType.slug)));
    targetRoomType.replaceChildren(new Option("Chọn thể loại đích", ""), ...roomTypes.map((roomType) => new Option(roomType.name, roomType.slug)));
    sourceRoomType.value = roomTypes.some((roomType) => roomType.slug === previousSource) ? previousSource : "";
    targetRoomType.value = roomTypes.some((roomType) => roomType.slug === previousTarget) ? previousTarget : "";
    const roomTypeSelect = document.querySelector("#roomType");
    const currentRoomType = roomTypeSelect.value;
    roomTypeSelect.replaceChildren(...roomTypes.map((roomType) => new Option(roomType.name, roomType.slug)));
    if (roomTypes.some((roomType) => roomType.slug === currentRoomType)) {
      roomTypeSelect.value = currentRoomType;
    }
    renderRoomTypes();
  } catch {
    roomTypeFormMessage.textContent = "Không thể tải thể loại phòng.";
  }
}

function formatCurrency(value) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(Number(value || 0));
}

function showSuccessToast(message) {
  successToastMessage.textContent = message;
  successToast.classList.remove("hidden");
  clearTimeout(successToastTimer);
  successToastTimer = setTimeout(() => successToast.classList.add("hidden"), 3500);
}

function renderDashboardAvatar(user) {
  const avatar = document.querySelector("#dashboardAvatar");
  const placeholder = document.querySelector("#dashboardAvatarPlaceholder");
  const initials = (user.full_name || "")
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
  placeholder.textContent = initials || "LS";
  avatar.onerror = () => {
    avatar.classList.add("hidden");
    placeholder.classList.remove("hidden");
  };
  if (user.avatar_url) {
    avatar.src = user.avatar_url;
    avatar.classList.remove("hidden");
    placeholder.classList.add("hidden");
  } else {
    avatar.removeAttribute("src");
    avatar.classList.add("hidden");
    placeholder.classList.remove("hidden");
  }
}

function showDashboard(user) {
  currentUser = user;
  document.querySelector("#userName").textContent = user.full_name;
  renderDashboardAvatar(user);
  document.querySelector("#userEmail").textContent = user.email;
  document.querySelector("#userRole").textContent = { manager: "Quản lý", staff: "Nhân viên" }[user.role] || user.role;
  authView.classList.add("hidden");
  registrationView.classList.add("hidden");
  passwordResetView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
  document.querySelector(".page-shell").classList.add("dashboard-mode");
  document.body.classList.add("dashboard-mode");
  setDashboardView("overview");
  renderRoomTypes();
  loadRoomTypes();
  loadRooms();
}

function showLogin(message = "") {
  dashboardView.classList.add("hidden");
  registrationView.classList.add("hidden");
  passwordResetView.classList.add("hidden");
  authView.classList.remove("hidden");
  document.querySelector(".page-shell").classList.remove("dashboard-mode");
  document.body.classList.remove("dashboard-mode");
  formMessageText.textContent = message;
  forgotPasswordLink.classList.add("hidden");
  formMessage.classList.toggle("success", Boolean(message));
}

function showPasswordReset() {
  dashboardView.classList.add("hidden");
  authView.classList.add("hidden");
  registrationView.classList.add("hidden");
  passwordResetView.classList.remove("hidden");
  document.querySelector(".page-shell").classList.remove("dashboard-mode");
  document.body.classList.remove("dashboard-mode");
  document.querySelector("#resetEmail").value = document.querySelector("#email").value.trim();
  passwordResetRequestMessage.textContent = "";
  passwordResetCompleteMessage.textContent = "";
  passwordResetCompleteForm.classList.add("hidden");
  passwordResetRequestForm.classList.remove("hidden");
}

function showRegistration() {
  authView.classList.add("hidden");
  dashboardView.classList.add("hidden");
  passwordResetView.classList.add("hidden");
  registrationView.classList.remove("hidden");
  registrationMessage.textContent = "";
}

function resetRoomForm() {
  roomForm.reset();
  const occupiedStatusOption = document.querySelector("#roomStatus option[value='occupied']");
  if (occupiedStatusOption) occupiedStatusOption.remove();
  roomForm.dataset.mode = "create";
  roomForm.dataset.roomId = "";
  roomFormTitle.textContent = "Thêm phòng";
  roomImageInput.required = true;
  roomImageName.textContent = "Chưa chọn tệp nào.";
  document.querySelector("#roomPrice").value = "1000000";
  document.querySelector("#roomFloor").value = "1";
  document.querySelector("#roomStatus").value = "available";
  document.querySelector("#roomStatus").disabled = true;
  roomFormMessage.textContent = "";
  roomFormMessage.classList.remove("success");
  roomFormPanel.classList.remove("is-open");
  roomFormModal.classList.add("hidden");
}

function openRoomForm(room = null) {
  roomFormModal.classList.remove("hidden");
  roomFormPanel.classList.add("is-open");
  const roomStatus = document.querySelector("#roomStatus");
  const occupiedStatusOption = roomStatus.querySelector("option[value='occupied']");
  if (occupiedStatusOption) occupiedStatusOption.remove();
  if (!room) {
    roomForm.reset();
    roomForm.dataset.mode = "create";
    roomForm.dataset.roomId = "";
    roomFormTitle.textContent = "Thêm phòng";
    roomImageInput.required = true;
    roomImageName.textContent = "Chưa chọn tệp nào.";
    document.querySelector("#roomPrice").value = "1000000";
    document.querySelector("#roomFloor").value = "1";
    document.querySelector("#roomStatus").value = "available";
    document.querySelector("#roomStatus").disabled = true;
    roomFormMessage.textContent = "";
    roomFormMessage.classList.remove("success");
    return;
  }

  roomForm.dataset.mode = "edit";
  roomForm.dataset.roomId = room.id;
  roomFormTitle.textContent = "Cập nhật phòng";
  document.querySelector("#roomCode").value = room.code || "";
  document.querySelector("#roomName").value = room.name || "";
  document.querySelector("#roomDescription").value = room.description || "";
  roomImageInput.value = "";
  roomImageInput.required = false;
  roomImageUrlInput.value = room.image_url || "";
  roomImageName.textContent = room.image_url ? "Ảnh hiện tại sẽ được giữ nếu không chọn ảnh mới." : "Chưa chọn tệp nào.";
  document.querySelector("#roomType").value = room.room_type || "double";
  document.querySelector("#roomFloor").value = room.floor || 1;
  document.querySelector("#roomPrice").value = room.price || 0;
  const hasActiveRental = Boolean(room.check_in);
  if (room.status === "occupied" && hasActiveRental) {
    const option = document.createElement("option");
    option.value = "occupied";
    option.textContent = "Đã thuê";
    option.disabled = true;
    roomStatus.append(option);
    roomStatus.value = "occupied";
    roomStatus.disabled = true;
  } else {
    roomStatus.value = room.status === "occupied" ? "available" : room.status || "available";
    roomStatus.disabled = false;
  }
  roomFormMessage.textContent = "";
  roomFormMessage.classList.remove("success");
}

function openDeleteConfirmation(roomId, trigger) {
  const room = (window.__roomList || []).find((item) => String(item.id) === String(roomId));
  if (!room) return;

  deleteConfirmTitle.textContent = "Xóa phòng";
  deleteConfirmKicker.textContent = "XÁC NHẬN THAO TÁC";
  cancelDeleteButton.textContent = "Hủy";
  confirmDeleteButton.classList.remove("hidden");
  pendingDeleteRoomId = room.id;
  pendingDeleteRoomTypeSlug = null;
  pendingDeleteRentalId = null;
  deleteTrigger = trigger;
  deleteConfirmMessage.textContent = `Bạn có chắc chắn muốn xóa phòng ${room.code}?`;
  deleteConfirmMessage.classList.remove("error");
  deleteConfirmModal.classList.remove("hidden");
  cancelDeleteButton.focus();
}

function openRoomTypeDeleteConfirmation(slug, name, trigger) {
  deleteConfirmTitle.textContent = "Xóa thể loại phòng";
  deleteConfirmKicker.textContent = "XÁC NHẬN THAO TÁC";
  cancelDeleteButton.textContent = "Hủy";
  confirmDeleteButton.textContent = "Xóa thể loại";
  confirmDeleteButton.classList.remove("hidden");
  pendingDeleteRoomId = null;
  pendingDeleteRoomTypeSlug = slug;
  pendingDeleteRentalId = null;
  deleteTrigger = trigger;
  deleteConfirmMessage.textContent = `Bạn có chắc chắn muốn xóa thể loại "${name}"?`;
  deleteConfirmMessage.classList.remove("error");
  deleteConfirmModal.classList.remove("hidden");
  cancelDeleteButton.focus();
}

function showDeleteBlockedNotice(trigger, message = "Phòng này hiện tại không thể xóa.") {
  deleteConfirmTitle.textContent = "Không thể xóa";
  deleteConfirmKicker.textContent = "THÔNG BÁO";
  deleteConfirmMessage.textContent = message;
  deleteConfirmMessage.classList.add("error");
  cancelDeleteButton.textContent = "Đóng";
  confirmDeleteButton.classList.add("hidden");
  pendingDeleteRoomId = null;
  pendingDeleteRoomTypeSlug = null;
  pendingDeleteRentalId = null;
  deleteTrigger = trigger;
  deleteConfirmModal.classList.remove("hidden");
  cancelDeleteButton.focus();
}

function showDeleteSuccessNotice() {
  deleteConfirmTitle.textContent = "Xóa thành công";
  deleteConfirmKicker.textContent = "THÔNG BÁO";
  deleteConfirmMessage.textContent = "Xóa phòng thành công";
  deleteConfirmMessage.classList.remove("error");
  cancelDeleteButton.textContent = "Đóng";
  confirmDeleteButton.classList.add("hidden");
  pendingDeleteRoomId = null;
  pendingDeleteRoomTypeSlug = null;
  pendingDeleteRentalId = null;
  deleteTrigger = null;
  deleteConfirmModal.classList.remove("hidden");
  cancelDeleteButton.focus();
}

function closeDeleteConfirmation() {
  deleteConfirmModal.classList.add("hidden");
  deleteConfirmTitle.textContent = "Xóa phòng";
  deleteConfirmKicker.textContent = "XÁC NHẬN THAO TÁC";
  deleteConfirmMessage.classList.remove("error");
  cancelDeleteButton.textContent = "Hủy";
  confirmDeleteButton.textContent = "Xác nhận";
  confirmDeleteButton.classList.remove("hidden");
  pendingDeleteRoomId = null;
  pendingDeleteRoomTypeSlug = null;
  pendingDeleteRentalId = null;
  if (deleteTrigger?.isConnected) deleteTrigger.focus();
  deleteTrigger = null;
}

function openUpcomingRentalDeleteConfirmation(rentalId, roomCode, trigger) {
  pendingDeleteRoomId = null;
  pendingDeleteRoomTypeSlug = null;
  pendingDeleteRentalId = rentalId;
  deleteTrigger = trigger;
  deleteConfirmTitle.textContent = "Xóa lịch đặt trước?";
  deleteConfirmKicker.textContent = "XÁC NHẬN THAO TÁC";
  deleteConfirmMessage.textContent = `Bạn có chắc chắn muốn xóa lịch đặt trước của phòng ${roomCode}?`;
  deleteConfirmMessage.classList.remove("error");
  cancelDeleteButton.textContent = "Hủy";
  confirmDeleteButton.textContent = "Xóa lịch";
  confirmDeleteButton.classList.remove("hidden");
  deleteConfirmModal.classList.remove("hidden");
  cancelDeleteButton.focus();
}

function countRoomsByStatus(rooms) {
  const counts = {
    all: rooms.length,
    available: 0,
    occupied: 0,
    cleaning: 0,
    maintenance: 0,
  };

  rooms.forEach((room) => {
    if (counts[room.status] !== undefined) {
      counts[room.status] += 1;
    }
  });

  return counts;
}

function renderRoomStatusFilters() {
  const rooms = window.__roomList || [];
  const counts = countRoomsByStatus(rooms);
  const statusOrder = [
    { key: "all", label: "Tất cả" },
    { key: "available", label: "Trống" },
    { key: "occupied", label: "Đã thuê" },
    { key: "cleaning", label: "Đang dọn" },
    { key: "maintenance", label: "Bảo trì" },
  ];

  document.querySelectorAll(".chip").forEach((button) => {
    const status = statusOrder.find((item) => item.key === button.dataset.filter) || statusOrder[0];
    const count = counts[status.key] ?? 0;
    button.innerHTML = `
      <span>${status.label}</span>
      <span class="chip-count">${count}</span>
    `;
    button.classList.toggle("has-count", true);
  });
}

function localDateTimeValue(date) {
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return offsetDate.toISOString().slice(0, 16);
}

function formatRentalTime(value) {
  if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value)) return "--:--";
  const [hour, minute] = value.split(":").map(Number);
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(2000, 0, 1, hour, minute));
}

function nextDateValue(dateTimeValue) {
  const [year, month, day] = dateTimeValue.slice(0, 10).split("-").map(Number);
  return localDateTimeValue(new Date(year, month - 1, day + 1)).slice(0, 10);
}

function updateRentalDateConstraints() {
  const nowValue = localDateTimeValue(new Date());
  const today = nowValue.slice(0, 10);
  rentalStartDateInput.min = today;
  const minimumTime = rentalStartDateInput.value === today
    ? nowValue.slice(11, 16)
    : "";
  const validTime = /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(rentalStartTimeInput.value);
  rentalStartTimeInput.setCustomValidity(
    minimumTime && validTime && rentalStartTimeInput.value < minimumTime
      ? "Giờ thuê phòng không được trước thời gian hiện tại."
      : "",
  );
  rentalEndInput.min = rentalStartDateInput.value
    ? nextDateValue(`${rentalStartDateInput.value}T00:00`)
    : nextDateValue(`${today}T00:00`);
}

function getRentalNights() {
  if (!rentalStartDateInput.value || !rentalEndInput.value) return 0;
  const [startYear, startMonth, startDay] = rentalStartDateInput.value.split("-").map(Number);
  const [endYear, endMonth, endDay] = rentalEndInput.value.split("-").map(Number);
  return (Date.UTC(endYear, endMonth - 1, endDay) - Date.UTC(startYear, startMonth - 1, startDay)) / 86400000;
}

function updateRentalSummary() {
  const room = (window.__roomList || []).find((item) => String(item.id) === rentalRoomIdInput.value);
  const nights = getRentalNights();
  if (!room || nights < 1) {
    rentalDuration.textContent = "Thời lượng: 0 đêm";
    rentalTotal.textContent = `Tổng tiền: ${formatCurrency(0)}`;
    return;
  }

  rentalDuration.textContent = `Thời lượng: ${nights} đêm`;
  rentalTotal.textContent = `Tổng tiền: ${formatCurrency(nights * room.price)}`;
}

function updateRentalRoomDetails() {
  const room = (window.__roomList || []).find((item) => String(item.id) === rentalRoomIdInput.value);
  if (!room) {
    rentalRoomDetails.innerHTML = '<p>Thông tin phòng sẽ hiển thị tại đây.</p>';
    updateRentalSummary();
    return;
  }
  const roomStatus = room.status === "occupied"
    ? "Đang có lịch thuê; có thể đặt khung giờ khác."
    : "Trạng thái: Trống";
  rentalRoomDetails.innerHTML = `
    <img src="${escapeHtml(room.image_url || "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80")}" alt="${escapeHtml(room.name)}">
    <strong>${escapeHtml(room.name)} · ${escapeHtml(room.code)}</strong>
    <span>${escapeHtml(room.description || "Khách sạn Lotus Stay.")}</span>
    <span>Loại: ${escapeHtml(roomTypeMap[room.room_type] || room.room_type)} · Tầng ${escapeHtml(room.floor)}</span>
    <span>${roomStatus}</span>
    <span>Giá: ${formatCurrency(room.price)} / đêm</span>
  `;
  updateRentalSummary();
}

function renderRentalRoomResults() {
  const searchTerm = rentalRoomInput.value.trim().toLocaleLowerCase();
  const matchingRooms = (window.__roomList || []).filter((room) =>
    ["available", "occupied"].includes(room.status)
      && room.code.toLocaleLowerCase().includes(searchTerm),
  );
  rentalRoomResults.replaceChildren();

  if (!searchTerm) {
    rentalRoomResults.classList.add("hidden");
    rentalRoomInput.setAttribute("aria-expanded", "false");
    return;
  }

  if (!matchingRooms.length) {
    const emptyMessage = document.createElement("p");
    emptyMessage.className = "rental-room-no-results";
    emptyMessage.textContent = "Không tìm thấy phòng phù hợp.";
    rentalRoomResults.append(emptyMessage);
  } else {
    matchingRooms.forEach((room) => {
      const option = document.createElement("button");
      option.className = "rental-room-result";
      option.type = "button";
      option.role = "option";
      option.dataset.roomId = room.id;
      option.textContent = `${room.code} · ${room.name}`;
      rentalRoomResults.append(option);
    });
  }

  rentalRoomResults.classList.remove("hidden");
  rentalRoomInput.setAttribute("aria-expanded", "true");
}

function selectRentalRoom(roomId) {
  const room = (window.__roomList || []).find((item) =>
    String(item.id) === roomId && ["available", "occupied"].includes(item.status),
  );
  if (!room) return;

  rentalRoomInput.value = room.code;
  rentalRoomIdInput.value = room.id;
  rentalRoomInput.setCustomValidity("");
  rentalRoomResults.classList.add("hidden");
  rentalRoomInput.setAttribute("aria-expanded", "false");
  updateRentalRoomDetails();
}

function openRentalForm() {
  rentalForm.reset();
  rentalRoomIdInput.value = "";
  rentalRoomResults.replaceChildren();
  rentalRoomResults.classList.add("hidden");
  rentalRoomInput.setAttribute("aria-expanded", "false");
  rentalRoomInput.setCustomValidity("");
  if (!(window.__roomList || []).some((room) => ["available", "occupied"].includes(room.status))) {
    rentalRoomInput.placeholder = "Không có phòng có thể đặt";
  } else {
    rentalRoomInput.placeholder = "Nhập mã phòng để tìm lịch trống";
  }
  const startsAt = new Date();
  const startsAtValue = localDateTimeValue(startsAt);
  rentalStartDateInput.value = startsAtValue.slice(0, 10);
  rentalStartTimeInput.value = startsAtValue.slice(11, 16);
  updateRentalDateConstraints();
  rentalEndInput.value = rentalEndInput.min;
  rentalCheckoutTime.textContent = formatRentalTime(rentalStartTimeInput.value);
  rentalFormMessage.textContent = "";
  rentalFormModal.classList.remove("hidden");
  updateRentalRoomDetails();
  rentalRoomInput.focus();
}

function closeRentalForm() {
  rentalFormModal.classList.add("hidden");
  rentalFormMessage.textContent = "";
}

async function saveRental(event) {
  event.preventDefault();
  rentalFormMessage.textContent = "";
  updateRentalDateConstraints();
  if (!rentalRoomIdInput.value) {
    rentalRoomInput.setCustomValidity("Vui lòng tìm và chọn một mã phòng trong danh sách.");
  } else {
    rentalRoomInput.setCustomValidity("");
  }
  updateRentalSummary();
  if (!rentalForm.reportValidity()) return;
  const nights = getRentalNights();
  if (nights < 1) {
    rentalFormMessage.textContent = "Ngày trả phòng phải sau ngày thuê phòng.";
    return;
  }
  const startsAt = `${rentalStartDateInput.value}T${rentalStartTimeInput.value}`;
  const endsAt = `${rentalEndInput.value}T${rentalStartTimeInput.value}`;

  const submitButton = rentalForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  try {
    const response = await fetch("/api/rentals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_name: rentalCustomerName.value.trim(),
        customer_phone: rentalCustomerPhone.value.trim(),
        customer_identity: document.querySelector("#rentalCustomerIdentity").value.trim(),
        room_id: Number(rentalRoomIdInput.value),
        starts_at: startsAt,
        ends_at: endsAt,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      rentalFormMessage.textContent = result.message || "Không thể lưu thông tin thuê phòng.";
      return;
    }
    closeRentalForm();
    await loadRooms();
    showSuccessToast(result.message);
  } catch {
    rentalFormMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  } finally {
    submitButton.disabled = false;
  }
}

function applyRoomFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll(".chip").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === filter);
  });
  renderRooms();
  renderOverviewRooms();
}

function renderRooms() {
  const rooms = window.__roomList || [];
  const filteredRooms = currentFilter === "all" ? rooms : rooms.filter((room) => room.status === currentFilter);

  if (!filteredRooms.length) {
    roomsGrid.innerHTML = '<article class="room-card room-empty"><div class="room-meta"><h4>Không có phòng nào</h4><p>Thử thay đổi bộ lọc hoặc thêm một phòng mới.</p></div></article>';
    return;
  }

  roomsGrid.innerHTML = filteredRooms.map((room) => `
    <article class="room-card">
      <div class="room-card-top">
        <span class="room-code">${room.code}</span>
        <span class="room-status status-${room.status}">${roomStatusMap[room.status] || room.status}</span>
      </div>
      <img src="${room.image_url || 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80'}" alt="${room.name}">
      <div class="room-meta">
        <h4>${room.name}</h4>
        <p>${room.description || "Khách sạn Lotus Stay."}</p>
      </div>
      <div class="room-footer">
        <span class="room-type type-${escapeHtml(room.room_type)}">${escapeHtml(roomTypeMap[room.room_type] || room.room_type)}</span>
        <strong>${formatCurrency(room.price)}</strong>
      </div>
      <div class="room-actions">
        <button class="mini-button" type="button" data-action="edit" data-room-id="${room.id}">Cập nhật</button>
        <button class="mini-button danger" type="button" data-action="delete" data-room-id="${room.id}">Xóa</button>
      </div>
    </article>
  `).join("");
}

function renderOverviewRooms() {
  const rooms = window.__roomList || [];
  const filteredRooms = currentFilter === "all" ? rooms : rooms.filter((room) => room.status === currentFilter);

  if (!filteredRooms.length) {
    overviewRoomsGrid.innerHTML = '<article class="overview-room-card room-empty"><strong>Chưa có phòng</strong><span>Không có phòng nào trong trạng thái này.</span></article>';
    return;
  }

  overviewRoomsGrid.innerHTML = filteredRooms.map((room) => {
    const overviewStatusMap = {
      available: { className: "is-available", label: "Phòng trống" },
      occupied: { className: "is-occupied", label: "Đã có người thuê" },
      cleaning: { className: "is-cleaning", label: "Đang dọn" },
      maintenance: { className: "is-maintenance", label: "Bảo trì" },
    };
    const status = overviewStatusMap[room.status] || overviewStatusMap.maintenance;
    const now = Date.now();
    const upcomingRental = (room.rentals || []).find((rental) => {
      const startsAt = new Date(rental.starts_at).getTime();
      return rental.status === "active" && startsAt > now && startsAt - now <= 60 * 60 * 1000;
    });
    const isUpcomingSoon = room.status === "available" && Boolean(upcomingRental);
    const formatOverviewDateTime = (value) => {
      if (!value) return "<strong>Chưa có</strong>";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "<strong>Chưa có</strong>";
      const dateLabel = new Intl.DateTimeFormat("vi-VN", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }).format(date);
      const timeLabel = new Intl.DateTimeFormat("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      }).format(date);
      return `<strong class="overview-room-time"><span>${dateLabel}</span><span>${timeLabel}</span></strong>`;
    };
    return `
      <article class="overview-room-card ${status.className}${isUpcomingSoon ? " is-upcoming-soon" : ""}"${room.rentals?.length ? ` data-room-id="${room.id}" role="button" tabindex="0" aria-label="Xem lịch thuê phòng ${escapeHtml(room.code)}"` : ""}>
        <div class="overview-room-heading">
          <strong>${room.code}</strong>
          <span class="overview-room-status">${isUpcomingSoon ? "Sắp có khách" : status.label}</span>
        </div>
        <div class="overview-room-details">
          <div><span>Giờ vào</span>${formatOverviewDateTime(room.check_in)}</div>
          <div><span>Giờ ra</span>${formatOverviewDateTime(room.check_out)}</div>
        </div>
      </article>
    `;
  }).join("");
}

function formatRentalDetailsDateTime(value) {
  if (!value) return "Chưa có";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Chưa có";
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(date);
}

function normalizeHistorySearchValue(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLocaleLowerCase("vi");
}

function renderRentalHistory() {
  const rows = document.querySelector("#rentalHistoryRows");
  const searchTerm = normalizeHistorySearchValue(rentalHistorySearch.value.trim());
  if (rentalHistoryError) {
    rows.innerHTML = `<tr><td class="history-empty is-error" colspan="8">${escapeHtml(rentalHistoryError)}</td></tr>`;
    return;
  }
  if (!rentalHistoryRentals.length) {
    rows.innerHTML = '<tr><td class="history-empty" colspan="8">Chưa có lượt thuê nào đã kết thúc.</td></tr>';
    return;
  }

  const matches = rentalHistoryRentals.filter((rental) => {
    const searchableValues = [
      rental.room_code,
      rental.room_name,
      rental.customer_name,
      rental.customer_phone,
      rental.customer_identity,
      formatRentalDetailsDateTime(rental.starts_at),
      formatRentalDetailsDateTime(rental.ends_at),
      rental.nights,
      formatCurrency(rental.total_price),
    ];
    return normalizeHistorySearchValue(searchableValues.join(" ")).includes(searchTerm);
  });
  if (!matches.length) {
    rows.innerHTML = '<tr><td class="history-empty" colspan="8">Không tìm thấy lượt thuê phù hợp.</td></tr>';
    return;
  }
  rows.innerHTML = matches.map((rental) => `
    <tr>
      <td><strong>${escapeHtml(rental.room_code)}</strong><small>${escapeHtml(rental.room_name)}</small></td>
      <td>${escapeHtml(rental.customer_name || "Chưa có thông tin")}</td>
      <td>${escapeHtml(rental.customer_phone || "Chưa có thông tin")}</td>
      <td>${escapeHtml(rental.customer_identity || "Chưa có thông tin")}</td>
      <td>${escapeHtml(formatRentalDetailsDateTime(rental.starts_at))}</td>
      <td>${escapeHtml(formatRentalDetailsDateTime(rental.ends_at))}</td>
      <td>${escapeHtml(rental.nights)}</td>
      <td><strong>${escapeHtml(formatCurrency(rental.total_price))}</strong></td>
    </tr>
  `).join("");
}

async function loadRentalHistory() {
  const rows = document.querySelector("#rentalHistoryRows");
  rentalHistoryError = "";
  rows.innerHTML = '<tr><td class="history-empty" colspan="8">Đang tải lịch sử thuê phòng...</td></tr>';
  try {
    const response = await fetch("/api/rentals/history");
    const result = await response.json();
    if (!response.ok) {
      rentalHistoryError = result.message || "Không thể tải lịch sử thuê phòng.";
      rentalHistoryRentals = [];
      renderRentalHistory();
      return;
    }
    rentalHistoryRentals = result.rentals;
    renderRentalHistory();
  } catch {
    rentalHistoryError = "Không thể kết nối máy chủ để tải lịch sử thuê phòng.";
    rentalHistoryRentals = [];
    renderRentalHistory();
  }
}

function renderTransferRoomResults() {
  const searchTerm = transferRoomSearch.value.trim().toLowerCase();
  const showResults = searchTerm.length > 0 && transferTargetRoomId === null;
  const currentRoom = (window.__roomList || []).find(
    (room) => String(room.id) === String(rentalDetailsRoomId),
  );
  const availableTargets = (window.__roomList || []).filter((room) => (
    String(room.id) !== String(rentalDetailsRoomId)
    && ["available", "occupied"].includes(room.status)
    && room.code.toLowerCase().includes(searchTerm)
  ));

  transferRoomResults.replaceChildren();
  availableTargets.slice(0, 5).forEach((room) => {
    const option = document.createElement("button");
    option.className = "transfer-room-option";
    option.type = "button";
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", String(room.id === transferTargetRoomId));
    option.textContent = room.code;
    option.addEventListener("click", () => {
      transferTargetRoomId = room.id;
      transferRoomSearch.value = room.code;
      transferRoomSelected.textContent = `Phòng đích: ${room.code}`;
      rentalTransferDropzone.textContent = `Kéo lịch sắp tới vào đây để chuyển sang phòng ${room.code}.`;
      rentalTransferDropzone.classList.add("is-ready");
      rentalTransferMessage.textContent = "";
      rentalTransferMessage.classList.remove("is-error", "is-success");
      renderTransferRoomResults();
    });
    transferRoomResults.append(option);
  });

  if (!availableTargets.length) {
    const emptyMessage = document.createElement("p");
    emptyMessage.className = "transfer-room-empty";
    emptyMessage.textContent = currentRoom
      ? "Không tìm thấy phòng đích phù hợp."
      : "Không tìm thấy phòng.";
    transferRoomResults.append(emptyMessage);
  } else if (availableTargets.length > 5) {
    const refineMessage = document.createElement("p");
    refineMessage.className = "transfer-room-empty";
    refineMessage.textContent = "Nhập thêm ký tự để thu hẹp kết quả.";
    transferRoomResults.append(refineMessage);
  }

  transferRoomResults.classList.toggle("hidden", !showResults);
  transferRoomSearch.setAttribute("aria-expanded", String(showResults));
}

function openRentalDetails(room) {
  if (rentalDetailsRoomId !== room.id) {
    transferTargetRoomId = null;
    transferRoomSearch.value = "";
    transferRoomSelected.textContent = "Chọn phòng đích để bắt đầu.";
    rentalTransferDropzone.textContent = "Chọn phòng đích, sau đó kéo lịch sắp tới vào đây.";
    rentalTransferDropzone.classList.remove("is-ready", "is-dragging");
    rentalTransferMessage.textContent = "";
    rentalTransferMessage.classList.remove("is-error", "is-success");
  }
  rentalDetailsRoomId = room.id;
  document.querySelector("#rentalDetailsTitle").textContent = `Lịch thuê phòng ${room.code}`;
  const rentalsList = rentalDetailsList;
  const now = new Date();
  const currentRental = (room.rentals || []).find((rental) => (
    rental.status === "active"
    && new Date(rental.starts_at) <= now
    && now < new Date(rental.ends_at)
  ));
  checkoutCurrentRentalButton.dataset.rentalId = currentRental ? String(currentRental.id) : "";
  checkoutCurrentRentalButton.disabled = !currentRental;
  rentalCheckoutMessage.textContent = "";
  rentalsList.replaceChildren();
  (room.rentals || []).forEach((rental) => {
    const startsAt = new Date(rental.starts_at);
    const endsAt = new Date(rental.ends_at);
    const status = startsAt <= now && now < endsAt
      ? "Đang thuê"
      : startsAt > now
        ? "Sắp tới"
        : "Đã kết thúc";
    const upcomingAndActive = rental.status === "active" && startsAt > now;
    const item = document.createElement("article");
    item.className = "rental-details-item";
    if (upcomingAndActive) item.classList.add("is-draggable");
    const rentalToggle = document.createElement("div");
    rentalToggle.className = "rental-details-summary";
    if (upcomingAndActive) {
      rentalToggle.draggable = true;
      rentalToggle.dataset.rentalId = rental.id;
      rentalToggle.classList.add("is-draggable");
      rentalToggle.setAttribute("aria-label", `Lịch sắp tới, kéo để chuyển phòng. ${formatRentalDetailsDateTime(rental.starts_at)}`);
    }
    const statusLabel = document.createElement("strong");
    statusLabel.className = `rental-status-label ${startsAt <= now && now < endsAt ? "is-current" : startsAt > now ? "is-upcoming" : "is-completed"}`;
    statusLabel.textContent = status;
    const rentalTimes = document.createElement("span");
    rentalTimes.className = "rental-summary-times";
    [
      ["Thuê", rental.starts_at],
      ["Trả", rental.ends_at],
    ].forEach(([label, value]) => {
      const time = document.createElement("span");
      time.className = "rental-summary-time";
      const timeLabel = document.createElement("small");
      const timeValue = document.createElement("strong");
      timeLabel.textContent = label;
      timeValue.textContent = formatRentalDetailsDateTime(value);
      time.append(timeLabel, timeValue);
      rentalTimes.append(time);
    });
    rentalToggle.append(statusLabel, rentalTimes);
    const expandButton = document.createElement("button");
    expandButton.className = "rental-details-toggle";
    expandButton.type = "button";
    expandButton.textContent = "＋";
    expandButton.setAttribute("aria-label", "Xem chi tiết lịch thuê");
    expandButton.setAttribute("aria-expanded", "false");
    expandButton.setAttribute("aria-controls", `rentalDetailsContent-${rental.id}`);
    expandButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const isExpanded = item.classList.toggle("is-expanded");
      details.hidden = !isExpanded;
      expandButton.textContent = isExpanded ? "−" : "＋";
      expandButton.setAttribute("aria-expanded", String(isExpanded));
      expandButton.setAttribute(
        "aria-label",
        isExpanded ? "Thu gọn chi tiết lịch thuê" : "Xem chi tiết lịch thuê",
      );
    });
    const details = document.createElement("dl");
    details.className = "rental-details-expanded";
    details.id = `rentalDetailsContent-${rental.id}`;
    details.hidden = true;
    [
      ["Tên khách", rental.customer_name || "Chưa có thông tin"],
      ["Số điện thoại", rental.customer_phone || "Chưa có thông tin"],
      ["CCCD", rental.customer_identity || "Chưa có thông tin"],
      ["Ngày giờ thuê", formatRentalDetailsDateTime(rental.starts_at)],
      ["Ngày giờ trả phòng", formatRentalDetailsDateTime(rental.ends_at)],
    ].forEach(([label, value]) => {
      const row = document.createElement("div");
      const term = document.createElement("dt");
      const description = document.createElement("dd");
      term.textContent = label;
      description.textContent = value;
      row.append(term, description);
      details.append(row);
    });
    item.append(rentalToggle, expandButton);
    if (upcomingAndActive) {
      const deleteButton = document.createElement("button");
      deleteButton.className = "rental-delete-button";
      deleteButton.type = "button";
      deleteButton.textContent = "−";
      deleteButton.setAttribute("aria-label", `Xóa lịch đặt trước phòng ${room.code}`);
      deleteButton.title = "Xóa lịch đặt trước";
      deleteButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        openUpcomingRentalDeleteConfirmation(rental.id, room.code, deleteButton);
      });
      item.append(deleteButton);
    }
    item.append(details);
    rentalsList.append(item);
  });
  if (!rentalsList.childElementCount) {
    const emptyMessage = document.createElement("p");
    emptyMessage.textContent = "Phòng chưa có lượt thuê.";
    rentalsList.append(emptyMessage);
  }
  document.querySelector("#toggleRentalTransfer").setAttribute(
    "aria-expanded",
    String(!rentalTransferPanel.classList.contains("hidden")),
  );
  renderTransferRoomResults();
  rentalDetailsModal.classList.remove("hidden");
  document.querySelector("#closeRentalDetails").focus();
}

function closeRentalDetails() {
  rentalDetailsModal.classList.add("hidden");
}

async function transferUpcomingRental(rentalId) {
  if (!transferTargetRoomId) {
    rentalTransferMessage.textContent = "Vui lòng tìm và chọn phòng đích.";
    rentalTransferMessage.classList.add("is-error");
    return;
  }
  rentalTransferMessage.textContent = "";
  rentalTransferMessage.classList.remove("is-error", "is-success");
  try {
    const response = await fetch(`/api/rentals/${rentalId}/transfer`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_room_id: transferTargetRoomId }),
    });
    const result = await response.json();
    if (!response.ok) {
      rentalTransferMessage.textContent = result.message === "Thời gian trùng lặp."
        ? "Thời gian trùng lặp"
        : result.message || "Không thể chuyển lịch thuê.";
      rentalTransferMessage.classList.add("is-error");
      return;
    }
    rentalTransferMessage.textContent = result.message;
    rentalTransferMessage.classList.add("is-success");
    await loadRooms();
    const updatedRoom = (window.__roomList || []).find(
      (room) => room.id === rentalDetailsRoomId,
    );
    if (updatedRoom) openRentalDetails(updatedRoom);
    showSuccessToast(result.message);
  } catch {
    rentalTransferMessage.textContent = "Không thể kết nối máy chủ. Lịch vẫn ở phòng cũ.";
    rentalTransferMessage.classList.add("is-error");
  }
}

async function checkoutCurrentRental() {
  const rentalId = Number(checkoutCurrentRentalButton.dataset.rentalId);
  if (!Number.isInteger(rentalId) || rentalId < 1) return;

  checkoutCurrentRentalButton.disabled = true;
  rentalCheckoutMessage.textContent = "";
  try {
    const response = await fetch(`/api/rentals/${rentalId}/checkout`, { method: "POST" });
    const result = await response.json();
    if (!response.ok) {
      rentalCheckoutMessage.textContent = result.message || "Không thể trả phòng.";
      checkoutCurrentRentalButton.disabled = false;
      return;
    }

    await loadRooms();
    const updatedRoom = (window.__roomList || []).find(
      (room) => room.id === rentalDetailsRoomId,
    );
    if (updatedRoom) openRentalDetails(updatedRoom);
    showSuccessToast(result.message);
  } catch {
    rentalCheckoutMessage.textContent = "Không thể kết nối máy chủ. Chưa thể trả phòng.";
    checkoutCurrentRentalButton.disabled = false;
  }
}

function openCheckoutConfirmation() {
  const room = (window.__roomList || []).find((item) => item.id === rentalDetailsRoomId);
  if (!room || !checkoutCurrentRentalButton.dataset.rentalId) return;
  checkoutConfirmMessage.textContent = `Bạn có chắc chắn muốn trả phòng ${room.code} không?`;
  checkoutConfirmModal.classList.remove("hidden");
  cancelCheckoutButton.focus();
}

function closeCheckoutConfirmation() {
  checkoutConfirmModal.classList.add("hidden");
  checkoutCurrentRentalButton.focus();
}

async function loadRooms() {
  try {
    const response = await fetch("/api/rooms");
    const result = await response.json();
    if (!response.ok) {
      roomFormMessage.textContent = result.message || "Không thể tải dữ liệu phòng.";
      return;
    }
    window.__roomList = result.rooms || [];
    renderRoomStatusFilters();
    renderRoomTypes();
    renderRooms();
    renderOverviewRooms();
  } catch {
    roomFormMessage.textContent = "Không thể tải danh sách phòng.";
  }
}

async function saveRoom(event) {
  event.preventDefault();
  roomFormMessage.textContent = "";
  roomFormMessage.classList.remove("success");
  if (!roomForm.reportValidity()) return;

  const formData = new FormData(roomForm);

  const mode = roomForm.dataset.mode || "create";
  const endpoint = mode === "edit" ? `/api/rooms/${roomForm.dataset.roomId}` : "/api/rooms";
  const method = mode === "edit" ? "PUT" : "POST";

  try {
    const response = await fetch(endpoint, {
      method,
      body: formData,
    });
    const result = await response.json();
    if (!response.ok) {
      roomFormMessage.textContent = result.message || "Dữ liệu phòng không hợp lệ.";
      return;
    }

    if (mode === "edit") {
      showSuccessToast("Cập nhật thành công.");
      resetRoomForm();
    } else {
      roomFormMessage.textContent = result.message;
      roomFormMessage.classList.add("success");
      resetRoomForm();
    }
    await loadRooms();
  } catch {
    roomFormMessage.textContent = "Không thể lưu phòng. Vui lòng thử lại.";
  }
}

roomImageInput.addEventListener("change", () => {
  const selectedFile = roomImageInput.files[0];
  roomImageName.textContent = selectedFile
    ? selectedFile.name
    : roomForm.dataset.mode === "edit" && roomImageUrlInput.value
      ? "Ảnh hiện tại sẽ được giữ nếu không chọn ảnh mới."
      : "Chưa chọn tệp nào.";
});

async function deleteRoom(roomId) {
  try {
    const response = await fetch(`/api/rooms/${roomId}`, { method: "DELETE" });
    const result = await response.json();
    if (!response.ok) {
      deleteConfirmMessage.textContent = result.message || "Xóa phòng thất bại.";
      deleteConfirmMessage.classList.add("error");
      return;
    }
    await loadRooms();
    showDeleteSuccessNotice();
  } catch {
    deleteConfirmMessage.textContent = "Không thể xóa phòng. Vui lòng thử lại.";
    deleteConfirmMessage.classList.add("error");
  }
}

async function deleteUpcomingRental(rentalId) {
  try {
    const response = await fetch(`/api/rentals/${rentalId}`, { method: "DELETE" });
    const result = await response.json();
    if (!response.ok) {
      deleteConfirmMessage.textContent = result.message || "Không thể xóa lịch thuê.";
      deleteConfirmMessage.classList.add("error");
      return;
    }

    closeDeleteConfirmation();
    await loadRooms();
    const updatedRoom = (window.__roomList || []).find(
      (room) => room.id === rentalDetailsRoomId,
    );
    if (updatedRoom) openRentalDetails(updatedRoom);
    showSuccessToast(result.message);
  } catch {
    deleteConfirmMessage.textContent = "Không thể kết nối máy chủ. Lịch thuê chưa được xóa.";
    deleteConfirmMessage.classList.add("error");
  }
}

async function deleteRoomType(slug, trigger) {
  if (trigger) trigger.disabled = true;
  try {
    const response = await fetch(`/api/room-types/${encodeURIComponent(slug)}`, { method: "DELETE" });
    const result = await response.json();
    if (!response.ok) {
      showDeleteBlockedNotice(trigger, result.message || "Không thể xóa thể loại phòng này.");
      return;
    }

    if (selectedRoomType === slug) selectedRoomType = null;
    await loadRoomTypes();
    closeDeleteConfirmation();
    showSuccessToast(result.message);
  } catch {
    showDeleteBlockedNotice(trigger, "Không thể xóa thể loại phòng này. Vui lòng thử lại.");
  } finally {
    if (trigger?.isConnected) trigger.disabled = false;
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  formMessageText.textContent = "";
  forgotPasswordLink.classList.add("hidden");
  const submitButton = loginForm.querySelector("button[type='submit']");
  submitButton.disabled = true;

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.querySelector("#email").value,
        password: document.querySelector("#password").value,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      formMessageText.textContent = result.message;
      forgotPasswordLink.classList.toggle("hidden", response.status !== 401);
      formMessage.classList.remove("success");
      return;
    }
    loginForm.reset();
    formMessage.classList.remove("success");
    showDashboard(result.user);
  } catch {
    formMessageText.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  } finally {
    submitButton.disabled = false;
  }
});

registrationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  registrationMessage.textContent = "";
  if (!registrationForm.reportValidity()) return;

  const password = document.querySelector("#registerPassword").value;
  const confirmPassword = document.querySelector("#confirmPassword").value;
  if (password !== confirmPassword) {
    registrationMessage.textContent = "Mật khẩu xác nhận không khớp.";
    return;
  }

  const submitButton = registrationForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  try {
    const response = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: document.querySelector("#fullName").value,
        email: document.querySelector("#registerEmail").value,
        password,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      registrationMessage.textContent = result.message;
      return;
    }
    document.querySelector("#email").value = document.querySelector("#registerEmail").value.trim();
    registrationForm.reset();
    showLogin(result.message);
  } catch {
    registrationMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  } finally {
    submitButton.disabled = false;
  }
});

document.querySelector("#showRegistration").addEventListener("click", showRegistration);
document.querySelector("#showLogin").addEventListener("click", () => showLogin());

function closeAccountMenu() {
  accountMenuDropdown.classList.add("hidden");
  accountMenuTrigger.setAttribute("aria-expanded", "false");
}

accountMenuTrigger.addEventListener("click", () => {
  const isOpen = !accountMenuDropdown.classList.contains("hidden");
  accountMenuDropdown.classList.toggle("hidden", isOpen);
  accountMenuTrigger.setAttribute("aria-expanded", String(!isOpen));
});
document.addEventListener("click", (event) => {
  if (!accountMenu.contains(event.target)) closeAccountMenu();
  if (!dashboardAvatarMenu.contains(event.target)) closeAvatarActions();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !accountMenuDropdown.classList.contains("hidden")) {
    closeAccountMenu();
    accountMenuTrigger.focus();
  }
  if (event.key === "Escape" && !dashboardAvatarActions.classList.contains("hidden")) {
    closeAvatarActions();
    dashboardAvatarButton.focus();
  }
  if (event.key === "Escape" && !avatarViewModal.classList.contains("hidden")) {
    closeAvatarView();
  }
  if (event.key === "Escape" && !rentalDetailsModal.classList.contains("hidden")) {
    closeRentalDetails();
  }
});

logoutButton.addEventListener("click", async () => {
  closeAccountMenu();
  await fetch("/api/logout", { method: "POST" });
  showLogin();
});

function renderProfileAvatar(avatarUrl) {
  if (avatarUrl) {
    profileAvatarPreview.src = avatarUrl;
    profileAvatarPreview.classList.remove("hidden");
    profileAvatarPlaceholder.classList.add("hidden");
  } else {
    profileAvatarPreview.removeAttribute("src");
    profileAvatarPreview.classList.add("hidden");
    profileAvatarPlaceholder.classList.remove("hidden");
  }
}

function closeAvatarActions() {
  dashboardAvatarActions.classList.add("hidden");
  dashboardAvatarButton.setAttribute("aria-expanded", "false");
}

function openAvatarView() {
  closeAvatarActions();
  const avatarUrl = currentUser?.avatar_url;
  if (avatarUrl) {
    avatarViewImage.src = avatarUrl;
    avatarViewImage.classList.remove("hidden");
    avatarViewPlaceholder.classList.add("hidden");
    avatarViewImage.onerror = () => {
      avatarViewImage.classList.add("hidden");
      avatarViewPlaceholder.textContent = "Không thể tải ảnh đại diện.";
      avatarViewPlaceholder.classList.remove("hidden");
    };
  } else {
    avatarViewImage.removeAttribute("src");
    avatarViewImage.classList.add("hidden");
    avatarViewPlaceholder.textContent = "Chưa có ảnh đại diện.";
    avatarViewPlaceholder.classList.remove("hidden");
  }
  avatarViewModal.classList.remove("hidden");
  document.querySelector("#closeAvatarView").focus();
}

function closeAvatarView() {
  avatarViewModal.classList.add("hidden");
  dashboardAvatarButton.focus();
}

function fillProfileForm(user) {
  currentUser = user;
  document.querySelector("#profileFullName").value = user.full_name || "";
  document.querySelector("#profileBirthDate").value = user.date_of_birth || "";
  document.querySelector("#profileEmail").value = user.email || "";
  document.querySelector("#profilePhone").value = user.phone || "";
  profileAvatarInput.value = "";
  profileFormMessage.textContent = "";
  renderProfileAvatar(user.avatar_url);
}

async function openProfileForm(focusAvatar = false) {
  closeAccountMenu();
  closeAvatarActions();
  if (currentUser) fillProfileForm(currentUser);
  profileModal.classList.remove("hidden");
  (focusAvatar ? profileAvatarInput : document.querySelector("#profileFullName")).focus();
  if (focusAvatar) {
    profileAvatarInput.click();
    return;
  }
  try {
    const response = await fetch("/api/profile");
    const result = await response.json();
    if (!response.ok) {
      profileFormMessage.textContent = result.message || "Không thể tải thông tin cá nhân.";
      return;
    }
    fillProfileForm(result.user);
    if (focusAvatar) profileAvatarInput.focus();
  } catch {
    profileFormMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  }
}

function closeProfileForm() {
  profileModal.classList.add("hidden");
  if (currentUser) fillProfileForm(currentUser);
  document.querySelector("#openProfileButton").focus();
}

dashboardAvatarButton.addEventListener("click", () => {
  const isOpen = !dashboardAvatarActions.classList.contains("hidden");
  dashboardAvatarActions.classList.toggle("hidden", isOpen);
  dashboardAvatarButton.setAttribute("aria-expanded", String(!isOpen));
});
document.querySelector("#viewAvatarButton").addEventListener("click", openAvatarView);
document.querySelector("#changeAvatarButton").addEventListener("click", () => openProfileForm(true));
document.querySelector("#closeAvatarView").addEventListener("click", closeAvatarView);
avatarViewModal.addEventListener("click", (event) => {
  if (event.target === avatarViewModal) closeAvatarView();
});
overviewRoomsGrid.addEventListener("click", (event) => {
  const card = event.target.closest(".overview-room-card[data-room-id]");
  if (!card) return;
  const room = (window.__roomList || []).find((item) => String(item.id) === card.dataset.roomId);
  if (room?.rentals?.length) openRentalDetails(room);
});
overviewRoomsGrid.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  const card = event.target.closest(".overview-room-card[data-room-id]");
  if (!card) return;
  event.preventDefault();
  const room = (window.__roomList || []).find((item) => String(item.id) === card.dataset.roomId);
  if (room?.rentals?.length) openRentalDetails(room);
});
document.querySelector("#closeRentalDetails").addEventListener("click", closeRentalDetails);
checkoutCurrentRentalButton.addEventListener("click", openCheckoutConfirmation);
cancelCheckoutButton.addEventListener("click", closeCheckoutConfirmation);
confirmCheckoutButton.addEventListener("click", () => {
  checkoutConfirmModal.classList.add("hidden");
  checkoutCurrentRental();
});
document.querySelector("#toggleRentalTransfer").addEventListener("click", (event) => {
  const isOpening = rentalTransferPanel.classList.contains("hidden");
  rentalTransferPanel.classList.toggle("hidden", !isOpening);
  event.currentTarget.setAttribute("aria-expanded", String(isOpening));
  if (isOpening) transferRoomSearch.focus();
});
transferRoomSearch.addEventListener("input", () => {
  transferTargetRoomId = null;
  transferRoomSelected.textContent = "Chọn phòng đích để bắt đầu.";
  rentalTransferDropzone.textContent = "Chọn phòng đích, sau đó kéo lịch sắp tới vào đây.";
  rentalTransferDropzone.classList.remove("is-ready");
  rentalTransferMessage.textContent = "";
  rentalTransferMessage.classList.remove("is-error", "is-success");
  renderTransferRoomResults();
});
rentalDetailsList.addEventListener("dragstart", (event) => {
  const rentalSummary = event.target.closest(".rental-details-summary[data-rental-id]");
  if (!rentalSummary) return;
  event.dataTransfer.setData("text/plain", rentalSummary.dataset.rentalId);
  event.dataTransfer.effectAllowed = "move";
  rentalTransferDropzone.classList.add("is-dragging");
});
rentalDetailsList.addEventListener("dragend", () => {
  rentalTransferDropzone.classList.remove("is-dragging");
});
rentalTransferDropzone.addEventListener("dragover", (event) => {
  if (!transferTargetRoomId) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  rentalTransferDropzone.classList.add("is-dragging");
});
rentalTransferDropzone.addEventListener("dragleave", (event) => {
  if (!rentalTransferDropzone.contains(event.relatedTarget)) {
    rentalTransferDropzone.classList.remove("is-dragging");
  }
});
rentalTransferDropzone.addEventListener("drop", async (event) => {
  event.preventDefault();
  rentalTransferDropzone.classList.remove("is-dragging");
  const rentalId = Number(event.dataTransfer.getData("text/plain"));
  if (Number.isInteger(rentalId) && rentalId > 0) {
    await transferUpcomingRental(rentalId);
  }
});
document.querySelector("#openProfileButton").addEventListener("click", () => openProfileForm());
document.querySelector("#cancelProfileForm").addEventListener("click", closeProfileForm);
profileAvatarInput.addEventListener("change", () => {
  const file = profileAvatarInput.files[0];
  if (!file) {
    renderProfileAvatar(currentUser?.avatar_url);
    return;
  }
  if (file.size > 5 * 1024 * 1024 || !["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
    profileAvatarInput.value = "";
    profileFormMessage.textContent = "Chọn ảnh JPG, PNG hoặc WebP có dung lượng tối đa 5 MB.";
    return;
  }
  profileAvatarPreview.src = URL.createObjectURL(file);
  profileAvatarPreview.classList.remove("hidden");
  profileAvatarPlaceholder.classList.add("hidden");
  profileFormMessage.textContent = "";
});
profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  profileFormMessage.textContent = "";
  if (!profileAvatarInput.files.length) {
    profileFormMessage.textContent = "Vui lòng chọn ảnh đại diện.";
    profileAvatarInput.focus();
    return;
  }
  const phone = document.querySelector("#profilePhone").value.trim();
  if (!/^\d+$/.test(phone)) {
    profileFormMessage.textContent = "Số điện thoại chỉ được nhập chữ số.";
    document.querySelector("#profilePhone").focus();
    return;
  }
  if (phone.length > 10) {
    profileFormMessage.textContent = "Số điện thoại không được vượt quá 10 chữ số.";
    document.querySelector("#profilePhone").focus();
    return;
  }
  if (phone.length < 10) {
    profileFormMessage.textContent = "Số điện thoại phải có đủ 10 chữ số.";
    document.querySelector("#profilePhone").focus();
    return;
  }
  if (!profileForm.reportValidity()) return;
  saveProfileButton.disabled = true;
  try {
    const response = await fetch("/api/profile", {
      method: "PUT",
      body: new FormData(profileForm),
    });
    const result = await response.json();
    if (!response.ok) {
      profileFormMessage.textContent = result.message || "Không thể cập nhật thông tin cá nhân.";
      return;
    }
    currentUser = result.user;
    document.querySelector("#userName").textContent = currentUser.full_name;
    renderDashboardAvatar(currentUser);
    fillProfileForm(currentUser);
    profileModal.classList.add("hidden");
    showSuccessToast(result.message);
  } catch {
    profileFormMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  } finally {
    saveProfileButton.disabled = false;
  }
});

document.querySelector("#openRoomForm").addEventListener("click", () => openRoomForm());
document.querySelector("#openRentalForm").addEventListener("click", openRentalForm);
document.querySelector("#cancelRentalForm").addEventListener("click", closeRentalForm);
rentalRoomInput.addEventListener("input", () => {
  rentalRoomIdInput.value = "";
  rentalRoomInput.setCustomValidity("");
  renderRentalRoomResults();
  updateRentalRoomDetails();
});
rentalRoomInput.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown") {
    const firstResult = rentalRoomResults.querySelector(".rental-room-result");
    if (firstResult) {
      event.preventDefault();
      firstResult.focus();
    }
  } else if (event.key === "Escape") {
    rentalRoomResults.classList.add("hidden");
    rentalRoomInput.setAttribute("aria-expanded", "false");
  }
});
rentalRoomResults.addEventListener("click", (event) => {
  const option = event.target.closest(".rental-room-result");
  if (option) selectRentalRoom(option.dataset.roomId);
});
rentalRoomResults.addEventListener("mousedown", (event) => {
  if (event.target.closest(".rental-room-result")) event.preventDefault();
});
rentalRoomResults.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    rentalRoomResults.classList.add("hidden");
    rentalRoomInput.setAttribute("aria-expanded", "false");
    rentalRoomInput.focus();
  }
});
rentalHistorySearch.addEventListener("input", renderRentalHistory);
rentalEndInput.addEventListener("input", updateRentalSummary);
rentalStartDateInput.addEventListener("input", () => {
  const nowValue = localDateTimeValue(new Date());
  if (
    rentalStartDateInput.value === nowValue.slice(0, 10)
    && /^\d{2}:\d{2}$/.test(rentalStartTimeInput.value)
    && rentalStartTimeInput.value < nowValue.slice(11, 16)
  ) {
    rentalStartTimeInput.value = nowValue.slice(11, 16);
  }
  updateRentalDateConstraints();
  if (rentalEndInput.value && rentalEndInput.value < rentalEndInput.min) {
    rentalEndInput.value = rentalEndInput.min;
  }
  updateRentalSummary();
});
function syncRentalCheckoutTime() {
  updateRentalDateConstraints();
  rentalCheckoutTime.textContent = formatRentalTime(rentalStartTimeInput.value);
}
rentalStartTimeInput.addEventListener("input", syncRentalCheckoutTime);
rentalStartTimeInput.addEventListener("change", syncRentalCheckoutTime);
rentalForm.addEventListener("submit", saveRental);
document.querySelector("#cancelRoomForm").addEventListener("click", resetRoomForm);
document.querySelectorAll(".nav-button[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    if (["overview", "rooms", "room-types", "history"].includes(button.dataset.view)) {
      setDashboardView(button.dataset.view);
    }
  });
});
const roomTypeForm = document.querySelector("#roomTypeForm");
document.querySelector("#openRoomTypeForm").addEventListener("click", () => {
  addRoomTypeModal.classList.remove("hidden");
  document.querySelector("#roomTypeName").focus();
});
document.querySelector("#cancelRoomTypeForm").addEventListener("click", () => {
  roomTypeForm.reset();
  addRoomTypeModal.classList.add("hidden");
  roomTypeFormMessage.textContent = "";
});
const moveRoomTypeForm = document.querySelector("#moveRoomTypeForm");
document.querySelector("#openMoveRoomTypeForm").addEventListener("click", () => {
  moveRoomTypeModal.classList.remove("hidden");
  renderMoveRoomChoices();
  document.querySelector("#sourceRoomType").focus();
});
document.querySelector("#cancelMoveRoomTypeForm").addEventListener("click", () => {
  moveRoomTypeForm.reset();
  moveRoomTypeModal.classList.add("hidden");
  moveRoomTypeFormMessage.textContent = "";
});
document.querySelector("#sourceRoomType").addEventListener("change", () => {
  moveRoomTypeFormMessage.textContent = "";
  renderMoveRoomChoices();
});
function closeMoveRoomTypeConfirmation() {
  moveRoomTypeConfirmModal.classList.add("hidden");
  pendingRoomTypeTransfer = null;
}

cancelMoveRoomTypeConfirmButton.addEventListener("click", closeMoveRoomTypeConfirmation);

confirmMoveRoomTypeButton.addEventListener("click", async () => {
  if (!pendingRoomTypeTransfer) return;
  const transfer = pendingRoomTypeTransfer;
  confirmMoveRoomTypeButton.disabled = true;
  cancelMoveRoomTypeConfirmButton.disabled = true;
  try {
    const response = await fetch("/api/room-types/move-rooms", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(transfer),
    });
    const result = await response.json();
    if (!response.ok) {
      moveRoomTypeFormMessage.textContent = result.message || "Không thể cập nhật thể loại phòng.";
      closeMoveRoomTypeConfirmation();
      return;
    }

    closeMoveRoomTypeConfirmation();
    moveRoomTypeForm.reset();
    moveRoomTypeModal.classList.add("hidden");
    await loadRooms();
    showSuccessToast(result.message);
  } catch {
    moveRoomTypeFormMessage.textContent = "Không thể cập nhật thể loại phòng. Vui lòng thử lại.";
    closeMoveRoomTypeConfirmation();
  } finally {
    confirmMoveRoomTypeButton.disabled = false;
    cancelMoveRoomTypeConfirmButton.disabled = false;
  }
});

moveRoomTypeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  moveRoomTypeFormMessage.textContent = "";
  if (!moveRoomTypeForm.reportValidity()) return;

  const sourceSlug = document.querySelector("#sourceRoomType").value;
  const targetSlug = document.querySelector("#targetRoomType").value;
  const roomIds = Array.from(
    moveRoomTypeForm.querySelectorAll('input[name="room_ids"]:checked'),
    (checkbox) => Number(checkbox.value),
  );
  if (!roomIds.length) {
    moveRoomTypeFormMessage.textContent = "Vui lòng chọn ít nhất một phòng cần chuyển.";
    return;
  }
  if (sourceSlug === targetSlug) {
    moveRoomTypeFormMessage.textContent = "Thể loại nguồn và đích phải khác nhau.";
    return;
  }
  const sourceName = roomTypeMap[sourceSlug];
  const targetName = roomTypeMap[targetSlug];
  pendingRoomTypeTransfer = {
    source_slug: sourceSlug,
    target_slug: targetSlug,
    room_ids: roomIds,
  };
  moveRoomTypeConfirmMessage.textContent = `Chuyển ${roomIds.length} phòng đã chọn từ "${sourceName}" sang "${targetName}"?`;
  moveRoomTypeConfirmModal.classList.remove("hidden");
  cancelMoveRoomTypeConfirmButton.focus();
});
roomTypeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  roomTypeFormMessage.textContent = "";
  if (!roomTypeForm.reportValidity()) return;

  try {
    const response = await fetch("/api/room-types", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: document.querySelector("#roomTypeName").value }),
    });
    const result = await response.json();
    if (!response.ok) {
      roomTypeFormMessage.textContent = result.message || "Không thể thêm thể loại phòng.";
      return;
    }

    roomTypeForm.reset();
    addRoomTypeModal.classList.add("hidden");
    await loadRoomTypes();
    showSuccessToast(result.message);
  } catch {
    roomTypeFormMessage.textContent = "Không thể thêm thể loại phòng. Vui lòng thử lại.";
  }
});
roomTypePickerTrigger.addEventListener("click", () => {
  const isOpen = !roomTypeList.classList.contains("hidden");
  roomTypeList.classList.toggle("hidden", isOpen);
  roomTypePickerTrigger.setAttribute("aria-expanded", String(!isOpen));
});
document.addEventListener("click", (event) => {
  if (!roomTypePickerControl.contains(event.target)) closeRoomTypePicker();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !roomTypeList.classList.contains("hidden")) {
    closeRoomTypePicker();
    roomTypePickerTrigger.focus();
  }
});
roomTypeList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const { action, roomType } = button.dataset;
  if (action === "select") {
    selectedRoomType = roomType;
    closeRoomTypePicker();
    renderRoomTypes();
    return;
  }

  const roomTypeName = roomTypeMap[roomType];
  if (action !== "delete" || !roomTypeName) return;
  closeRoomTypePicker();
  const roomCount = (window.__roomList || []).filter((room) => room.room_type === roomType).length;
  if (roomCount === 0) {
    openRoomTypeDeleteConfirmation(roomType, roomTypeName, button);
    return;
  }
  await deleteRoomType(roomType, button);
});
window.addEventListener("resize", fitRoomTypeResults);
roomForm.addEventListener("submit", saveRoom);
cancelDeleteButton.addEventListener("click", closeDeleteConfirmation);
confirmDeleteButton.addEventListener("click", async () => {
  if (pendingDeleteRentalId !== null) {
    confirmDeleteButton.disabled = true;
    await deleteUpcomingRental(pendingDeleteRentalId);
    confirmDeleteButton.disabled = false;
    return;
  }
  if (pendingDeleteRoomTypeSlug !== null) {
    confirmDeleteButton.disabled = true;
    await deleteRoomType(pendingDeleteRoomTypeSlug, deleteTrigger);
    confirmDeleteButton.disabled = false;
    return;
  }
  if (pendingDeleteRoomId === null) return;
  confirmDeleteButton.disabled = true;
  await deleteRoom(pendingDeleteRoomId);
  confirmDeleteButton.disabled = false;
});

roomsGrid.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const { action, roomId } = button.dataset;
  if (action === "edit") {
    const room = (window.__roomList || []).find((item) => String(item.id) === String(roomId));
    openRoomForm(room);
    return;
  }

  if (action === "delete") {
    const room = (window.__roomList || []).find((item) => String(item.id) === String(roomId));
    if (room && room.status !== "available") {
      showDeleteBlockedNotice(button);
      return;
    }
    if (room?.status === "available") openDeleteConfirmation(roomId, button);
  }
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => applyRoomFilter(chip.dataset.filter));
});

async function restoreSession() {
  try {
    const response = await fetch("/api/session");
    const result = await response.json();
    if (result.user) showDashboard(result.user);
    else showLogin();
  } catch {
    showLogin();
  }
}

resetRoomForm();
restoreSession();
setInterval(() => {
  if (currentUser && !document.hidden && !dashboardView.classList.contains("hidden")) {
    loadRooms();
  }
}, 30000);
document.addEventListener("visibilitychange", () => {
  if (currentUser && !document.hidden && !dashboardView.classList.contains("hidden")) {
    loadRooms();
  }
});

forgotPasswordLink.addEventListener("click", showPasswordReset);
document.querySelector("#backToLogin").addEventListener("click", () => showLogin());

passwordResetRequestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  passwordResetRequestMessage.textContent = "";
  if (!passwordResetRequestForm.reportValidity()) return;
  const submitButton = passwordResetRequestForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  try {
    const response = await fetch("/api/password-reset/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: document.querySelector("#resetEmail").value }),
    });
    const result = await response.json();
    passwordResetRequestMessage.textContent = result.message;
    if (response.ok) {
      passwordResetRequestMessage.classList.add("success");
      passwordResetCompleteForm.classList.remove("hidden");
      passwordResetRequestForm.classList.add("hidden");
      document.querySelector("#resetCode").focus();
    } else {
      passwordResetRequestMessage.classList.remove("success");
    }
  } catch {
    passwordResetRequestMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  } finally {
    submitButton.disabled = false;
  }
});

passwordResetCompleteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  passwordResetCompleteMessage.textContent = "";
  if (!passwordResetCompleteForm.reportValidity()) return;
  const newPassword = document.querySelector("#resetNewPassword").value;
  if (newPassword !== document.querySelector("#resetConfirmPassword").value) {
    passwordResetCompleteMessage.textContent = "Mật khẩu xác nhận không khớp.";
    return;
  }
  const submitButton = passwordResetCompleteForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  try {
    const response = await fetch("/api/password-reset/complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.querySelector("#resetEmail").value,
        code: document.querySelector("#resetCode").value,
        new_password: newPassword,
      }),
    });
    const result = await response.json();
    passwordResetCompleteMessage.textContent = result.message;
    if (response.ok) {
      showLogin(result.message);
    }
  } catch {
    passwordResetCompleteMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  } finally {
    submitButton.disabled = false;
  }
});