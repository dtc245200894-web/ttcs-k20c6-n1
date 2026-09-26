const authView = document.querySelector("#authView");
const registrationView = document.querySelector("#registrationView");
const dashboardView = document.querySelector("#dashboardView");
const loginForm = document.querySelector("#loginForm");
const registrationForm = document.querySelector("#registrationForm");
const formMessage = document.querySelector("#formMessage");
const registrationMessage = document.querySelector("#registrationMessage");

function showDashboard(user) {
  document.querySelector("#userName").textContent = user.full_name;
  document.querySelector("#userEmail").textContent = user.email;
  document.querySelector("#userRole").textContent = { manager: "Quản lý", staff: "Nhân viên" }[user.role] || user.role;
  authView.classList.add("hidden");
  registrationView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
}

function showLogin(message = "") {
  dashboardView.classList.add("hidden");
  registrationView.classList.add("hidden");
  authView.classList.remove("hidden");
  formMessage.textContent = message;
  formMessage.classList.toggle("success", Boolean(message));
}

function showRegistration() {
  authView.classList.add("hidden");
  dashboardView.classList.add("hidden");
  registrationView.classList.remove("hidden");
  registrationMessage.textContent = "";
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

async function restoreSession() {
  try {
    const response = await fetch("/api/session");
    const result = await response.json();
    if (result.user) showDashboard(result.user);
  } catch {
    showLogin();
  }
}

restoreSession();