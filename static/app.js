const authView = document.querySelector("#authView");
const registrationView = document.querySelector("#registrationView");
const dashboardView = document.querySelector("#dashboardView");
const loginForm = document.querySelector("#loginForm");
const registrationForm = document.querySelector("#registrationForm");
const formMessage = document.querySelector("#formMessage");
const registrationMessage = document.querySelector("#registrationMessage");
const roomsGrid = document.querySelector("#roomsGrid");
const overviewRoomsGrid = document.querySelector("#overviewRoomsGrid");
const roomForm = document.querySelector("#roomForm");
const roomFormPanel = document.querySelector("#roomFormPanel");
const roomFormModal = document.querySelector("#roomFormModal");
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
document.body.append(roomFormModal, addRoomTypeModal, moveRoomTypeModal, deleteConfirmModal, moveRoomTypeConfirmModal);
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
  };
  document.querySelector(".dashboard-header .kicker").textContent = `LOTUS STAY / ${viewLabels[view] || "TRANG CHỦ"}`;
  fitRoomTypeResults();
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
  const roomTypePicker = document.querySelector("#roomTypeCategory");
  const options = Object.entries(roomTypeMap).map(([type, label]) => {
    const count = rooms.filter((room) => room.room_type === type).length;
    return new Option(`${label} (${count} phòng)`, type);
  });
  roomTypePicker.replaceChildren(new Option("Chọn thể loại phòng", ""), ...options);
  roomTypePicker.value = selectedRoomType || "";
  renderTypeRooms();
  fitRoomTypeResults();
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

function showDashboard(user) {
  document.querySelector("#userName").textContent = user.full_name;
  document.querySelector("#userEmail").textContent = user.email;
  document.querySelector("#userRole").textContent = { manager: "Quản lý", staff: "Nhân viên" }[user.role] || user.role;
  authView.classList.add("hidden");
  registrationView.classList.add("hidden");
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
  authView.classList.remove("hidden");
  document.querySelector(".page-shell").classList.remove("dashboard-mode");
  document.body.classList.remove("dashboard-mode");
  formMessage.textContent = message;
  formMessage.classList.toggle("success", Boolean(message));
}

function showRegistration() {
  authView.classList.add("hidden");
  dashboardView.classList.add("hidden");
  registrationView.classList.remove("hidden");
  registrationMessage.textContent = "";
}

function resetRoomForm() {
  roomForm.reset();
  roomForm.dataset.mode = "create";
  roomForm.dataset.roomId = "";
  roomFormTitle.textContent = "Thêm phòng";
  document.querySelector("#roomPrice").value = "1000000";
  document.querySelector("#roomFloor").value = "1";
  document.querySelector("#roomStatus").value = "available";
  roomFormMessage.textContent = "";
  roomFormMessage.classList.remove("success");
  roomFormPanel.classList.remove("is-open");
  roomFormModal.classList.add("hidden");
}

function openRoomForm(room = null) {
  roomFormModal.classList.remove("hidden");
  roomFormPanel.classList.add("is-open");
  if (!room) {
    roomForm.reset();
    roomForm.dataset.mode = "create";
    roomForm.dataset.roomId = "";
    roomFormTitle.textContent = "Thêm phòng";
    document.querySelector("#roomPrice").value = "1000000";
    document.querySelector("#roomFloor").value = "1";
    document.querySelector("#roomStatus").value = "available";
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
  document.querySelector("#roomImage").value = room.image_url || "";
  document.querySelector("#roomType").value = room.room_type || "double";
  document.querySelector("#roomFloor").value = room.floor || 1;
  document.querySelector("#roomPrice").value = room.price || 0;
  document.querySelector("#roomStatus").value = room.status || "available";
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
  deleteTrigger = trigger;
  deleteConfirmMessage.textContent = `Bạn có chắc chắn muốn xóa phòng ${room.code}?`;
  deleteConfirmMessage.classList.remove("error");
  deleteConfirmModal.classList.remove("hidden");
  cancelDeleteButton.focus();
}

function showDeleteBlockedNotice(trigger) {
  deleteConfirmTitle.textContent = "Không thể xóa";
  deleteConfirmKicker.textContent = "THÔNG BÁO";
  deleteConfirmMessage.textContent = "Phòng này hiện tại không thể xóa.";
  deleteConfirmMessage.classList.add("error");
  cancelDeleteButton.textContent = "Đóng";
  confirmDeleteButton.classList.add("hidden");
  pendingDeleteRoomId = null;
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
  confirmDeleteButton.classList.remove("hidden");
  pendingDeleteRoomId = null;
  if (deleteTrigger?.isConnected) deleteTrigger.focus();
  deleteTrigger = null;
}

function applyRoomFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll(".chip").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === filter);
  });
  renderRooms();
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
        <button class="mini-button danger" type="button" data-action="delete" data-room-id="${room.id}" ${["available", "occupied", "cleaning"].includes(room.status) ? "" : 'disabled title="Chỉ xóa được phòng đang trống"'}>Xóa</button>
      </div>
    </article>
  `).join("");
}

function renderOverviewRooms() {
  const rooms = window.__roomList || [];

  if (!rooms.length) {
    overviewRoomsGrid.innerHTML = '<article class="overview-room-card room-empty"><strong>Chưa có phòng</strong><span>Hãy thêm phòng trong mục Quản lý phòng.</span></article>';
    return;
  }

  overviewRoomsGrid.innerHTML = rooms.map((room) => {
    const overviewStatusMap = {
      available: { className: "is-available", label: "Phòng trống" },
      occupied: { className: "is-occupied", label: "Đã có người thuê" },
      cleaning: { className: "is-cleaning", label: "Đang dọn" },
      maintenance: { className: "is-maintenance", label: "Bảo trì" },
    };
    const status = overviewStatusMap[room.status] || overviewStatusMap.maintenance;
    return `
      <article class="overview-room-card ${status.className}">
        <div class="overview-room-heading">
          <strong>${room.code}</strong>
          <span class="overview-room-status">${status.label}</span>
        </div>
        <div class="overview-room-details">
          <div><span>Giờ vào</span><strong>${room.check_in || "Chưa có"}</strong></div>
          <div><span>Giờ ra</span><strong>${room.check_out || "Chưa có"}</strong></div>
        </div>
      </article>
    `;
  }).join("");
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

  const formData = {
    code: document.querySelector("#roomCode").value,
    name: document.querySelector("#roomName").value,
    description: document.querySelector("#roomDescription").value,
    image_url: document.querySelector("#roomImage").value,
    room_type: document.querySelector("#roomType").value,
    floor: Number(document.querySelector("#roomFloor").value),
    price: Number(document.querySelector("#roomPrice").value),
    status: document.querySelector("#roomStatus").value,
  };

  const mode = roomForm.dataset.mode || "create";
  const endpoint = mode === "edit" ? `/api/rooms/${roomForm.dataset.roomId}` : "/api/rooms";
  const method = mode === "edit" ? "PUT" : "POST";

  try {
    const response = await fetch(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
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

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  formMessage.textContent = "";
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
      formMessage.textContent = result.message;
      formMessage.classList.remove("success");
      return;
    }
    loginForm.reset();
    formMessage.classList.remove("success");
    showDashboard(result.user);
  } catch {
    formMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
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

document.querySelector("#logoutButton").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  showLogin();
});

document.querySelector("#openRoomForm").addEventListener("click", () => openRoomForm());
document.querySelector("#cancelRoomForm").addEventListener("click", resetRoomForm);
document.querySelectorAll(".nav-button[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    if (["overview", "rooms", "room-types"].includes(button.dataset.view)) {
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
    selectedRoomType = transfer.target_slug;
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

    selectedRoomType = result.room_type.slug;
    roomTypeForm.reset();
    addRoomTypeModal.classList.add("hidden");
    await loadRoomTypes();
    showSuccessToast(result.message);
  } catch {
    roomTypeFormMessage.textContent = "Không thể thêm thể loại phòng. Vui lòng thử lại.";
  }
});
document.querySelector("#roomTypeCategory").addEventListener("change", (event) => {
  selectedRoomType = event.currentTarget.value || null;
  renderRoomTypes();
});
window.addEventListener("resize", fitRoomTypeResults);
roomForm.addEventListener("submit", saveRoom);
cancelDeleteButton.addEventListener("click", closeDeleteConfirmation);
confirmDeleteButton.addEventListener("click", async () => {
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
    if (room?.status === "occupied" || room?.status === "cleaning") {
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