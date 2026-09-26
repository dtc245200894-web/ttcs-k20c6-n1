const authView = document.querySelector("#authView");
const dashboardView = document.querySelector("#dashboardView");
const loginForm = document.querySelector("#loginForm");
const formMessage = document.querySelector("#formMessage");

function showDashboard(user) {
  document.querySelector("#userName").textContent = user.full_name;
  document.querySelector("#userEmail").textContent = user.email;
  document.querySelector("#userRole").textContent = user.role === "manager" ? "Quản lý" : user.role;
  authView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
}

function showLogin() {
  dashboardView.classList.add("hidden");
  authView.classList.remove("hidden");
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
      return;
    }
    loginForm.reset();
    showDashboard(result.user);
  } catch {
    formMessage.textContent = "Không thể kết nối máy chủ. Vui lòng thử lại.";
  } finally {
    submitButton.disabled = false;
  }
});

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