import { useEffect, useState } from 'react';
import { ThemeIcon } from '../../shared/ui/ThemeIcon';
import './landing.css';

type LandingTheme = 'light' | 'dark';

const LANDING_THEME_STORAGE_KEY = 'landing-theme';

function storedLandingTheme(): LandingTheme | null {
  const stored = window.localStorage.getItem(LANDING_THEME_STORAGE_KEY);
  return stored === 'light' || stored === 'dark' ? stored : null;
}

function systemPrefersDark(): boolean {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
}

export function appUrlForHostname(hostname: string): string {
  return ['your-fitness-coach.ru', 'www.your-fitness-coach.ru'].includes(hostname)
    ? 'https://app.your-fitness-coach.ru/app'
    : '/app';
}

const features = [
  {
    number: '01',
    label: 'Тренировка на сегодня',
    title: 'Откройте приложение и сразу переходите к делу',
    text: 'Упражнения, подходы, повторения, рабочий вес и отдых уже собраны в понятном плане занятия.',
    variant: 'wide',
  },
  {
    number: '02',
    label: 'Программы',
    title: 'Выберите путь под свою задачу',
    text: 'Назначьте себе готовую программу, создайте собственную или занимайтесь по плану тренера.',
    variant: 'standard',
  },
  {
    number: '03',
    label: 'Прогресс',
    title: 'Принимайте решения по своим результатам',
    text: 'История тренировок, рабочие веса, личные рекорды и показатели тела помогают видеть динамику.',
    variant: 'standard',
  },
  {
    number: '04',
    label: 'Питание',
    title: 'Получите ориентиры КБЖУ',
    text: 'Рассчитайте калории, белки, жиры и углеводы с учётом параметров, активности и цели.',
    variant: 'standard',
  },
  {
    number: '05',
    label: 'Упражнения',
    title: 'Сверяйтесь с техникой в нужный момент',
    text: 'Каталог и информация об упражнениях доступны прямо во время работы с программой.',
    variant: 'standard',
  },
  {
    number: '06',
    label: 'Для тренеров',
    title: 'Ведите своих клиентов в одном кабинете',
    text: 'Приглашайте клиентов, назначайте и корректируйте программы, отслеживайте тренировки, прогресс и показатели каждого человека.',
    variant: 'coach',
  },
];

const workflow = [
  [
    'Откройте веб-приложение',
    'Начните без установки: достаточно браузера на телефоне или компьютере.',
  ],
  ['Расскажите о себе', 'Укажите цель, уровень подготовки и основные параметры.'],
  ['Выберите свой путь', 'Готовая программа, собственный план или работа вместе с тренером.'],
  ['Тренируйтесь и фиксируйте', 'Подходы, повторения и рабочие веса сохраняются по ходу занятия.'],
  ['Следите за прогрессом', 'История и показатели помогают оценивать динамику и менять план.'],
];

export default function LandingPage() {
  const appUrl = appUrlForHostname(window.location.hostname);
  const [manualTheme, setManualTheme] = useState<LandingTheme | null>(storedLandingTheme);
  const [prefersDark, setPrefersDark] = useState(systemPrefersDark);
  const theme: LandingTheme = manualTheme ?? (prefersDark ? 'dark' : 'light');

  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'Your Fitness Coach — веб-приложение для тренировок и прогресса';
    document.body.classList.add('landing-mode');
    return () => {
      document.title = previousTitle;
      document.body.classList.remove('landing-mode');
    };
  }, []);

  useEffect(() => {
    if (!window.matchMedia) return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (event: MediaQueryListEvent) => setPrefersDark(event.matches);
    media.addEventListener?.('change', onChange);
    return () => media.removeEventListener?.('change', onChange);
  }, []);

  useEffect(() => {
    const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
    const previousColor = meta?.content;
    document.body.classList.toggle('landing-dark-mode', theme === 'dark');
    if (meta) meta.content = theme === 'dark' ? '#0d120f' : '#f1f3ec';
    return () => {
      document.body.classList.remove('landing-dark-mode');
      if (meta && previousColor) meta.content = previousColor;
    };
  }, [theme]);

  const toggleTheme = () => {
    const nextTheme: LandingTheme = theme === 'dark' ? 'light' : 'dark';
    window.localStorage.setItem(LANDING_THEME_STORAGE_KEY, nextTheme);
    setManualTheme(nextTheme);
  };

  return (
    <div className={`landing-page landing-page--${theme}`}>
      <header className="landing-header">
        <a className="landing-brand" href="#top" aria-label="Your Fitness Coach — на главную">
          <img
            className="landing-brand__mark"
            src="/assets/brand/fitness-logo-v2.png"
            alt=""
            width="36"
            height="36"
          />
          <span>Your Fitness Coach</span>
        </a>
        <nav className="landing-nav" aria-label="Навигация по странице">
          <a href="#features">Возможности</a>
          <a href="#how-it-works">Как это работает</a>
          <a href="#contact">Контакты</a>
        </nav>
        <div className="landing-header__actions">
          <button
            type="button"
            className="landing-theme-toggle"
            aria-label={theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему'}
            title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            onClick={toggleTheme}
          >
            <ThemeIcon theme={theme} />
          </button>
          <a className="landing-button landing-button--compact" href={appUrl}>
            Войти
          </a>
        </div>
      </header>

      <main id="top">
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-hero__copy">
            <p className="landing-kicker">Веб-приложение для тренировок и прогресса</p>
            <h1 id="landing-title">
              Знайте, что делать сегодня.
              <br />
              <span>Следите, как растёт прогресс.</span>
            </h1>
            <p className="landing-hero__lead">
              Программа тренировок, занятие на сегодня, ориентиры КБЖУ и история результатов — в
              одном веб-приложении. Тренируйтесь самостоятельно или работайте вместе с тренером.
            </p>
            <div className="landing-hero__actions">
              <a className="landing-button" href={appUrl}>
                Открыть приложение
                <span aria-hidden="true">↗</span>
              </a>
              <a className="landing-text-link" href="#how-it-works">
                Посмотреть, как всё устроено
              </a>
            </div>
            <p className="landing-hero__note">
              Начните в браузере <span aria-hidden="true">·</span> Telegram можно подключить для
              тренировок в зале и общения с тренером
            </p>
          </div>

          <div
            className="landing-hero__visual"
            aria-label="Пример интерфейса тренировки на сегодня"
          >
            <div className="landing-orbit landing-orbit--one" />
            <div className="landing-orbit landing-orbit--two" />
            <div className="landing-workout-demo">
              <div className="landing-workout-demo__top">
                <div>
                  <span className="landing-workout-demo__eyebrow">Сегодня · пример интерфейса</span>
                  <strong>Верх тела</strong>
                </div>
                <span className="landing-workout-demo__status">В процессе</span>
              </div>

              <div className="landing-workout-demo__summary">
                <span>3 упражнения</span>
                <span>4 из 9 подходов</span>
              </div>

              <div className="landing-workout-demo__exercise">
                <div className="landing-workout-demo__exercise-head">
                  <strong>Жим гантелей лёжа</strong>
                  <span>3 × 10 · отдых 90 сек.</span>
                </div>
                <div className="landing-workout-demo__sets" aria-label="Подходы жима гантелей">
                  <span className="is-complete">1</span>
                  <span className="is-complete">2</span>
                  <span>3</span>
                  <small>10 повторов · 18 кг</small>
                </div>
              </div>

              <div className="landing-workout-demo__exercise">
                <div className="landing-workout-demo__exercise-head">
                  <strong>Тяга верхнего блока</strong>
                  <span>3 × 12 · отдых 75 сек.</span>
                </div>
                <div
                  className="landing-workout-demo__sets"
                  aria-label="Подходы тяги верхнего блока"
                >
                  <span className="is-complete">1</span>
                  <span>2</span>
                  <span>3</span>
                  <small>12 повторов · 35 кг</small>
                </div>
              </div>
            </div>

            <div className="landing-rest-demo" aria-label="Пример таймера отдыха">
              <span>Отдых</span>
              <strong>01:24</strong>
              <small>Следующий подход</small>
            </div>
            <div className="landing-nutrition-demo">
              <span>Ориентир на день</span>
              <strong>КБЖУ</strong>
              <small>Рассчитывается по вашей цели</small>
            </div>
          </div>
        </section>

        <section className="landing-problem" aria-labelledby="landing-problem-title">
          <div className="landing-problem__copy">
            <p className="landing-kicker">Всё связано</p>
            <h2 id="landing-problem-title">Тренировки не должны жить в пяти разных местах.</h2>
            <p>
              Когда план, записи и результаты разделены, сложнее понять, что делать дальше. Your
              Fitness Coach связывает весь путь в одну систему.
            </p>
          </div>
          <div
            className="landing-problem__visual"
            aria-label="Один сервис вместо разных инструментов"
          >
            <div className="landing-problem__sources">
              <span>Когда всё разрозненно</span>
              <ul>
                <li>Заметки</li>
                <li>Таблицы</li>
                <li>Случайные программы</li>
                <li>Дневник показателей</li>
                <li>Ручной учёт результатов</li>
              </ul>
            </div>
            <div className="landing-problem__result">
              <span className="landing-flow-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M5 12h14m-5-5 5 5-5 5" />
                </svg>
              </span>
              <span>В Your Fitness Coach</span>
              <strong>Один понятный план действий</strong>
            </div>
          </div>
        </section>

        <section id="features" className="landing-section">
          <div className="landing-section__heading">
            <p className="landing-kicker">От возможностей к результату</p>
            <h2>Понятные действия для спортсмена и тренера</h2>
            <p>
              Занимающийся видит следующий шаг и фиксирует результат. Тренер управляет программами
              своих клиентов и получает общую картину без разрозненных отчётов.
            </p>
          </div>
          <div className="landing-feature-grid">
            {features.map((feature) => (
              <article
                className={`landing-feature landing-feature--${feature.variant}`}
                key={feature.number}
              >
                <div className="landing-feature__meta">
                  <span>{feature.number}</span>
                  <span>{feature.label}</span>
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="how-it-works" className="landing-section landing-workflow">
          <div className="landing-section__heading landing-section__heading--light">
            <p className="landing-kicker">Как это работает</p>
            <h2>От цели до понятного следующего шага</h2>
            <p>
              Начните самостоятельно или подключите тренера — базовый путь остаётся простым и
              последовательным.
            </p>
          </div>
          <ol>
            {workflow.map(([title, text], index) => (
              <li key={title}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="landing-platforms" aria-labelledby="landing-platforms-title">
          <div className="landing-platforms__intro">
            <p className="landing-kicker">Продолжайте в Telegram</p>
            <h2 id="landing-platforms-title">
              Основная работа — в браузере. Telegram — когда удобнее.
            </h2>
            <p>
              Тренировки, программы и прогресс доступны в веб-приложении. Telegram дополняет его
              быстрым доступом к занятию и внешним каналом общения с тренером.
            </p>
          </div>

          <div className="landing-platforms__options">
            <article className="landing-platform-card">
              <div className="landing-platform-card__top">
                <span className="landing-platform-card__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <rect x="3" y="4" width="18" height="14" rx="2" />
                    <path d="M8 21h8M12 18v3" />
                  </svg>
                </span>
                <span>Основное приложение</span>
              </div>
              <h3>Основные функции — в браузере</h3>
              <p>
                Настраивайте программы, выполняйте тренировки и анализируйте прогресс с телефона или
                компьютера.
              </p>
            </article>

            <div className="landing-platforms__sync" aria-label="Данные синхронизируются">
              <span className="landing-flow-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M4 8h16m-3-3 3 3-3 3M20 16H4m3-3-3 3 3 3" />
                </svg>
              </span>
              <strong>Один аккаунт</strong>
            </div>

            <article className="landing-platform-card landing-platform-card--telegram">
              <div className="landing-platform-card__top">
                <span className="landing-platform-card__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="m21 4-8.2 16-3.1-7.1L3 9.8 21 4Z" />
                    <path d="m9.7 12.9 4.8-4.3" />
                  </svg>
                </span>
                <span>Дополнение</span>
              </div>
              <h3>Тренировка и общение — в Telegram</h3>
              <p>
                Открывайте занятие в зале, отмечайте подходы и переходите к переписке со своим
                тренером в Telegram.
              </p>
            </article>
          </div>

          <p className="landing-platforms__note">
            Для самостоятельных тренировок Telegram не нужен <span aria-hidden="true">·</span>{' '}
            общение с тренером происходит в Telegram
          </p>
        </section>

        <section className="landing-audience" aria-label="Выберите подходящий сценарий">
          <article>
            <p className="landing-kicker">Занимаетесь самостоятельно?</p>
            <h2>Тренируйтесь по понятному плану в своём темпе</h2>
            <p>
              Выберите готовую программу или соберите свою. Выполняйте занятия и отслеживайте
              прогресс в браузере — Telegram для этого не нужен.
            </p>
            <a className="landing-button landing-audience__link" href={appUrl}>
              Начать самостоятельно <span aria-hidden="true">↗</span>
            </a>
          </article>
          <article>
            <p className="landing-kicker">Вы тренер?</p>
            <h2>Приглашайте клиентов и ведите их в одном кабинете</h2>
            <p>
              Клиент подключается по вашей ссылке. Назначайте программы, следите за выполнением и
              прогрессом, а для переписки переходите в Telegram.
            </p>
            <a className="landing-button landing-audience__link" href={appUrl}>
              Открыть кабинет тренера <span aria-hidden="true">↗</span>
            </a>
          </article>
        </section>

        <section id="contact" className="landing-contact">
          <div className="landing-contact__copy">
            <p className="landing-kicker">Начните в браузере</p>
            <h2>Откройте Your Fitness Coach и выберите свой путь</h2>
            <p>
              Зарегистрируйтесь как спортсмен или тренер. Для старта не нужны установка и Telegram.
            </p>
          </div>
          <div className="landing-contact__actions">
            <a className="landing-button landing-contact__primary" href={appUrl}>
              Перейти в веб-приложение <span aria-hidden="true">↗</span>
            </a>
            <a
              className="landing-contact__link"
              href="https://t.me/your_fitness_support_bot"
              target="_blank"
              rel="noreferrer"
            >
              <strong>Задать вопрос в Telegram</strong>
              <span aria-hidden="true">↗</span>
            </a>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <a className="landing-brand" href="#top">
          <img
            className="landing-brand__mark"
            src="/assets/brand/fitness-logo-v2.png"
            alt=""
            width="36"
            height="36"
          />
          <span>Your Fitness Coach</span>
        </a>
        <p>Тренировки и прогресс в веб-приложении. Общение с тренером — в Telegram.</p>
        <span>© {new Date().getFullYear()}</span>
      </footer>
    </div>
  );
}
