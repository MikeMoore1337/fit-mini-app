const params = new URLSearchParams(location.search);
const allowedScreens = new Set([
  "today-new",
  "today-workout",
  "today-rest",
  "program",
  "active-strength",
  "active-cardio",
  "nutrition-search",
  "nutrition-empty",
  "nutrition-barcode",
  "progress-data",
  "progress-empty",
  "profile-compact",
  "profile-expanded",
]);
const allowedFrames = new Set(["mobile", "tma"]);
const allowedThemes = new Set(["light", "dark"]);

const screen = allowedScreens.has(params.get("screen"))
  ? params.get("screen")
  : "today-workout";
const frame = allowedFrames.has(params.get("frame"))
  ? params.get("frame")
  : "mobile";
const theme = allowedThemes.has(params.get("theme"))
  ? params.get("theme")
  : "light";

document.documentElement.dataset.theme = theme;

const screenLabels = {
  "today-new": "Сегодня · новый пользователь",
  "today-workout": "Сегодня · запланированная тренировка",
  "today-rest": "Сегодня · день восстановления",
  program: "Программа тренировок",
  "active-strength": "Активная силовая тренировка",
  "active-cardio": "Активное кардио",
  "nutrition-search": "Питание · поиск продукта",
  "nutrition-empty": "Питание · пустой дневник",
  "nutrition-barcode": "Питание · штрихкод",
  "progress-data": "Прогресс · достаточно данных",
  "progress-empty": "Прогресс · недостаточно данных",
  "profile-compact": "Профиль · compact sections",
  "profile-expanded": "Профиль · expanded detail",
};

const directions = [
  ["a", "A", "Command Stack"],
  ["b", "B", "Day Rail"],
  ["c", "C", "Signal Grid"],
];

document.querySelector("#compareTitle").textContent = screenLabels[screen];
document.querySelector("#compareMeta").textContent =
  `${frame === "tma" ? "mocked TMA" : "Mobile Web"} · 390 × 844 · ${theme}`;

const grid = document.querySelector("#compareGrid");
const frames = directions.map(([variant, letter, label]) => {
  const section = document.createElement("section");
  section.className = "direction";
  const heading = document.createElement("div");
  heading.className = "direction-label";
  heading.innerHTML = `<b>${letter}</b><span>${label}</span>`;
  const iframe = document.createElement("iframe");
  iframe.title = `${label}: ${screenLabels[screen]}`;
  iframe.src = `./index.html?${new URLSearchParams({ variant, screen, frame, theme, presentation: "1", v: "owner-detail-13" })}`;
  section.append(heading, iframe);
  grid.append(section);
  return iframe;
});

Promise.all(
  frames.map(
    (iframe) =>
      new Promise((resolve) => {
        iframe.addEventListener("load", resolve, { once: true });
      }),
  ),
).then(() => {
  document.documentElement.dataset.ready = "true";
});
