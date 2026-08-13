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
  ['Заполните профиль', 'Укажите цель, уровень подготовки и актуальные параметры.'],
  ['Получите программу', 'Тренер составит план и распределит тренировки по расписанию.'],
  [
    'Фиксируйте результаты',
    'Отмечайте выполненные подходы, вес и повторения прямо во время занятия.',
  ],
  ['Двигайтесь дальше', 'Следите за динамикой вместе с тренером и адаптируйте план.'],
];

export default function LandingPage() {
  const appUrl = appUrlForHostname(window.location.hostname);
  const [manualTheme, setManualTheme] = useState<LandingTheme | null>(storedLandingTheme);
  const [prefersDark, setPrefersDark] = useState(systemPrefersDark);
  const theme: LandingTheme = manualTheme ?? (prefersDark ? 'dark' : 'light');

  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'Your Fitness Coach — тренировки и прогресс в браузере и Telegram';
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
            <p className="landing-kicker">Тренировки в браузере и Telegram</p>
            <h1 id="landing-title">
              Знайте, что делать сегодня.
              <br />
              <span>Следите, как растёт прогресс.</span>
            </h1>
            <p className="landing-hero__lead">
              Программа тренировок, занятие на сегодня, ориентиры КБЖУ и история результатов — в
              одном приложении. Тренируйтесь самостоятельно или вместе с тренером.
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
              Работает в браузере и Telegram <span aria-hidden="true">·</span> данные сохраняются в
              одном аккаунте
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
            <h2>От цели до измеримого результата</h2>
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

        <section className="landing-audience">
          <article>
            <p className="landing-kicker">Для клиентов</p>
            <h2>Сосредоточьтесь на тренировке, а не на организации</h2>
            <p>
              Актуальный план, история занятий, замеры и ориентиры по питанию всегда находятся в
              одном месте.
            </p>
          </article>
          <article>
            <p className="landing-kicker">Для тренеров</p>
            <h2>Управляйте сопровождением без лишней рутины</h2>
            <p>Создавайте программы, планируйте занятия и отслеживайте динамику каждого клиента.</p>
          </article>
        </section>

        <section id="contact" className="landing-contact">
          <div>
            <p className="landing-kicker">Начнём с диалога</p>
            <h2>Хотите узнать больше о Your Fitness Coach?</h2>
          </div>
          <a
            className="landing-contact__link"
            href="https://t.me/your_fitness_support_bot"
            target="_blank"
            rel="noreferrer"
          >
            <strong>Связаться в Telegram</strong>
            <span aria-hidden="true">↗</span>
          </a>
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
        <p>Персональные тренировки и связь с тренером в единой системе.</p>
        <span>© {new Date().getFullYear()}</span>
      </footer>
    </div>
  );
}
