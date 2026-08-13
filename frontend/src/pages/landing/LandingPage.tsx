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
    title: 'План всегда под рукой',
    text: 'Расписание, упражнения, подходы и рекомендации собраны в одном понятном пространстве.',
  },
  {
    number: '02',
    title: 'Прогресс без догадок',
    text: 'История тренировок, рабочие веса, замеры и личные результаты помогают видеть движение к цели.',
  },
  {
    number: '03',
    title: 'Тренер видит главное',
    text: 'Специалист следит за выполнением программы и вовремя корректирует нагрузку и питание.',
  },
  {
    number: '04',
    title: 'Удобно на любом устройстве',
    text: 'Занимайтесь через Telegram, а данные останутся доступны в едином защищённом аккаунте.',
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
    document.title = 'Your Fitness Coach — персональные тренировки с поддержкой тренера';
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
            <p className="landing-kicker">Тренировки с понятной системой</p>
            <h1 id="landing-title">
              Ваш прогресс.
              <br />
              <span>В фокусе тренера.</span>
            </h1>
            <p className="landing-hero__lead">
              Персональная программа, дневник результатов, питание и поддержка специалиста — в одном
              приложении без таблиц и разрозненных заметок.
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
          </div>

          <div
            className="landing-hero__visual"
            aria-label="Пример контроля тренировочного прогресса"
          >
            <div className="landing-orbit landing-orbit--one" />
            <div className="landing-orbit landing-orbit--two" />
            <div className="landing-dashboard">
              <div className="landing-dashboard__top">
                <div>
                  <span>Сегодня</span>
                  <strong>Верх тела</strong>
                </div>
                <span className="landing-dashboard__status">По плану</span>
              </div>
              <div className="landing-dashboard__chart" aria-hidden="true">
                {[34, 46, 42, 64, 58, 76, 88].map((height, index) => (
                  <span key={index} style={{ height: `${height}%` }} />
                ))}
              </div>
              <div className="landing-dashboard__metrics">
                <div>
                  <span>Тренировок</span>
                  <strong>12</strong>
                </div>
                <div>
                  <span>Серия</span>
                  <strong>4 недели</strong>
                </div>
              </div>
            </div>
            <div className="landing-float-card landing-float-card--coach">
              <span className="landing-avatar">М</span>
              <div>
                <small>Тренер</small>
                <strong>План обновлён</strong>
              </div>
              <span className="landing-check" aria-hidden="true">
                ✓
              </span>
            </div>
            <div className="landing-float-card landing-float-card--progress">
              <small>Прогресс за месяц</small>
              <strong>+18%</strong>
            </div>
          </div>
        </section>

        <section className="landing-proof" aria-label="Преимущества сервиса">
          <p>Один сервис вместо</p>
          <div>
            <span>таблиц</span>
            <span>заметок</span>
            <span>разрозненных планов</span>
            <span>потерянных результатов</span>
          </div>
        </section>

        <section id="features" className="landing-section">
          <div className="landing-section__heading">
            <p className="landing-kicker">Возможности</p>
            <h2>Всё необходимое, чтобы тренироваться последовательно</h2>
            <p>
              Клиент понимает, что делать сегодня. Тренер видит общую картину и принимает решения на
              основе результатов.
            </p>
          </div>
          <div className="landing-feature-grid">
            {features.map((feature) => (
              <article className="landing-feature" key={feature.number}>
                <span>{feature.number}</span>
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
