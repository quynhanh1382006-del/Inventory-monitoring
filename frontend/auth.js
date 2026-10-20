const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const message = document.getElementById("message");

function showMessage(text, success = false) {
    message.textContent = text;
    message.className = success ? "message success" : "message";
    message.style.display = "block";
}

async function sendRequest(url, data) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || result.message || "Có lỗi xảy ra");
    }

    return result;
}

document.getElementById("show-register").addEventListener("click", () => {
    loginForm.hidden = true;
    registerForm.hidden = false;
    message.style.display = "none";
});

document.getElementById("show-login").addEventListener("click", () => {
    registerForm.hidden = true;
    loginForm.hidden = false;
    message.style.display = "none";
});

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const data = Object.fromEntries(new FormData(loginForm));

    try {
        const result = await sendRequest("/api/login", data);
        showMessage("Đăng nhập thành công!", true);
        window.location.href = "/";
    } catch (error) {
        showMessage(error.message);
    }
});

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const data = Object.fromEntries(new FormData(registerForm));

    try {
        await sendRequest("/api/register", data);
        showMessage("Đăng ký thành công! Bạn có thể đăng nhập.", true);

        registerForm.reset();
        registerForm.hidden = true;
        loginForm.hidden = false;
    } catch (error) {
        showMessage(error.message);
    }
});

