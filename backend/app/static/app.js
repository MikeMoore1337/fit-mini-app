// ===== INIT =====

const tg = window.Telegram?.WebApp;

function log(...args) {
    console.log("[APP]", ...args);
}

function showError(text) {
    alert(text);
}

// ===== DEBUG =====

log("Telegram object:", tg);
log("initData:", tg?.initData);
log("initDataUnsafe:", tg?.initDataUnsafe);

// ===== STATE =====

let accessToken = null;

// ===== API =====

async function api(url, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
    };

    if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const res = await fetch(url, {
        ...options,
        headers,
    });

    if (!res.ok) {
        const text = await res.text();
        log("API ERROR:", res.status, text);
        throw new Error(`API error ${res.status}`);
    }

    return res.json();
}

// ===== AUTH =====

async function loginWithTelegram() {
    if (!tg || !tg.initData) {
        showError("Открой Mini App через Telegram");
        return;
    }

    try {
        log("Sending initData to backend...");

        const data = await api("/api/v1/auth/telegram/init", {
            method: "POST",
            body: JSON.stringify({
                init_data: tg.initData,
            }),
        });

        log("Auth response:", data);

        accessToken = data.access_token;

        document.getElementById("authState").innerText = "Авторизован ✅";

        await loadProfile();

    } catch (e) {
        console.error(e);
        showError("Ошибка авторизации");
    }
}

// ===== PROFILE =====

async function loadProfile() {
    try {
        const me = await api("/api/v1/me");
        log("Profile:", me);

        document.getElementById("full_name").value = me.full_name || "";
        document.getElementById("goal").value = me.goal || "";
        document.getElementById("level").value = me.level || "";
        document.getElementById("height_cm").value = me.height_cm || "";
        document.getElementById("weight_kg").value = me.weight_kg || "";
        document.getElementById("workouts_per_week").value = me.workouts_per_week || "";

    } catch (e) {
        log("No profile yet");
    }
}

// ===== SAVE PROFILE =====

async function saveProfile() {
    try {
        const payload = {
            full_name: document.getElementById("full_name").value,
            goal: document.getElementById("goal").value,
            level: document.getElementById("level").value,
            height_cm: Number(document.getElementById("height_cm").value),
            weight_kg: Number(document.getElementById("weight_kg").value),
            workouts_per_week: Number(document.getElementById("workouts_per_week").value),
        };

        await api("/api/v1/me/profile", {
            method: "PATCH",
            body: JSON.stringify(payload),
        });

        alert("Профиль сохранён");

    } catch (e) {
        console.error(e);
        alert("Ошибка сохранения профиля");
    }
}

// ===== INIT UI =====

document.getElementById("telegramLoginBtn")?.addEventListener("click", loginWithTelegram);
document.getElementById("saveProfileBtn")?.addEventListener("click", saveProfile);

// ===== AUTO LOGIN =====

(async () => {
    if (!tg) {
        log("NOT in Telegram WebApp");
        document.getElementById("authState").innerText = "Открой через Telegram";
        return;
    }

    tg.ready();
    tg.expand();

    if (!tg.initData) {
        log("initData is EMPTY");
        document.getElementById("authState").innerText = "Нет данных Telegram";
        return;
    }

    log("Auto login...");
    await loginWithTelegram();
})();