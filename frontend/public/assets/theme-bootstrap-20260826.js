document.documentElement.classList.replace('no-js', 'js');

(() => {
  const root = document.documentElement;
  const darkQuery = window.matchMedia?.('(prefers-color-scheme: dark)');
  let preference = 'system';
  try {
    const stored = localStorage.getItem('app-theme') ?? localStorage.getItem('landing-theme');
    if (stored === 'system' || stored === 'light' || stored === 'dark') preference = stored;
  } catch {
    // The system preference remains available when storage is blocked.
  }

  let colorScheme = preference === 'system' ? (darkQuery?.matches ? 'dark' : 'light') : preference;
  const search = new URLSearchParams(location.search);
  const hash = new URLSearchParams(location.hash.replace(/^#/, ''));
  const launchData = search.get('tgWebAppData') ?? hash.get('tgWebAppData');
  const rawThemeParams = search.get('tgWebAppThemeParams') ?? hash.get('tgWebAppThemeParams');
  if (launchData && rawThemeParams) {
    try {
      const background = JSON.parse(rawThemeParams).bg_color;
      if (/^#[\da-f]{6}$/i.test(background)) {
        const channels = [1, 3, 5].map((offset) =>
          Number.parseInt(background.slice(offset, offset + 2), 16),
        );
        const luminance =
          (channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722) / 255;
        colorScheme = luminance < 0.45 ? 'dark' : 'light';
        root.dataset.appSurface = 'telegram';
        root.dataset.themeSource = 'telegram-launch-fallback';
      }
    } catch {
      // The SDK applies the authoritative Telegram colorScheme before React renders.
    }
  }

  root.dataset.colorScheme = colorScheme;
  if (!root.dataset.appSurface) {
    root.dataset.themePreference = preference;
    root.dataset.themeSource = 'web';
  }
  const themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor) {
    themeColor.content = colorScheme === 'dark' ? '#0d120f' : '#f1f3ec';
  }
})();
