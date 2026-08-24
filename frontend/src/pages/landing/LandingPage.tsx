import { useEffect, useState } from 'react';
import { BrandLogo } from '../../shared/ui/BrandLogo';
import { PublicShell } from '../../shared/ui/PublicShell';
import { applyRouteMetadata } from '../../shared/seo/metadata';
import { appUrlForHostname, loginUrlForHostname } from '../../shared/navigation/appUrl';
import { AppLink } from '../../shared/navigation/router';
import { productEventSurface, trackProductEvent } from '../../shared/analytics/productEvents';
import './landing.css';

export { appUrlForHostname, loginUrlForHostname } from '../../shared/navigation/appUrl';

const features = [
  {
    number: '01',
    label: 'Тренировка на сегодня',
    title: 'Откройте приложение и сразу переходите к делу',
    text: 'Упражнения, подходы, повторения, рабочий вес и отдых уже собраны в понятном плане занятия.',
    variant: 'wide',
    path: '/training',
  },
  {
    number: '02',
    label: 'Программы',
    title: 'Выберите путь под свою задачу',
    text: 'Назначьте себе готовую программу, создайте собственную или занимайтесь по плану тренера.',
    variant: 'standard',
    path: '/training',
  },
  {
    number: '03',
    label: 'Прогресс',
    title: 'Принимайте решения по своим результатам',
    text: 'История тренировок, рабочие веса, личные рекорды и показатели тела помогают видеть динамику.',
    variant: 'standard',
    path: '/progress',
  },
  {
    number: '04',
    label: 'Питание',
    title: 'Получите ориентиры КБЖУ',
    text: 'Рассчитайте калории, белки, жиры и углеводы с учётом параметров, активности и цели.',
    variant: 'standard',
    path: '/nutrition',
  },
  {
    number: '05',
    label: 'Упражнения',
    title: 'Сверяйтесь с техникой в нужный момент',
    text: 'Каталог и информация об упражнениях доступны прямо во время работы с программой.',
    variant: 'standard',
    path: '/knowledge',
  },
  {
    number: '06',
    label: 'Для тренеров',
    title: 'Ведите своих клиентов в одном кабинете',
    text: 'После одобрения заявки приглашайте клиентов, назначайте и корректируйте программы, отслеживайте тренировки, прогресс и показатели каждого человека.',
    variant: 'coach',
    path: '/for-trainers',
  },
];

const workflow = [
  ['Откройте веб-приложение', 'Начните без установки: достаточно открыть приложение в браузере.'],
  ['Расскажите о себе', 'Укажите цель, уровень подготовки и основные параметры.'],
  ['Выберите свой путь', 'Готовая программа, собственный план или работа вместе с тренером.'],
  ['Тренируйтесь и фиксируйте', 'Подходы, повторения и рабочие веса сохраняются по ходу занятия.'],
  ['Следите за прогрессом', 'История и показатели помогают оценивать динамику и менять план.'],
];

export default function LandingPage() {
  const appUrl = appUrlForHostname(window.location.hostname);
  const loginUrl = loginUrlForHostname(window.location.hostname);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    applyRouteMetadata('/');
    trackProductEvent(
      { name: 'landing_viewed', surface: productEventSurface() },
      { dedupe: 'session' },
    );
  }, []);

  useEffect(() => {
    if (!mobileMenuOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileMenuOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [mobileMenuOpen]);

  return (
    <PublicShell
      className="landing-page"
      homeHref="#top"
      skipTarget="landing-content"
      headerNavigation={
        <nav
          id="landing-navigation"
          className={`landing-nav${mobileMenuOpen ? ' is-open' : ''}`}
          aria-label="Навигация по странице"
        >
          <a href="#features" onClick={() => setMobileMenuOpen(false)}>
            Возможности
          </a>
          <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)}>
            Как это работает
          </a>
          <a href="#contact" onClick={() => setMobileMenuOpen(false)}>
            Контакты
          </a>
        </nav>
      }
      headerAction={
        <>
          <a
            className="landing-button landing-button--compact"
            href={loginUrl}
            onClick={() =>
              trackProductEvent({ name: 'landing_login_selected', surface: productEventSurface() })
            }
          >
            Войти
          </a>
          <button
            type="button"
            className={`landing-menu-toggle${mobileMenuOpen ? ' is-open' : ''}`}
            aria-label={mobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
            aria-expanded={mobileMenuOpen}
            aria-controls="landing-navigation"
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
        </>
      }
    >
      <main id="landing-content" tabIndex={-1}>
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
              <a
                className="landing-button landing-action"
                href={appUrl}
                onClick={() =>
                  trackProductEvent({
                    name: 'landing_app_selected',
                    surface: productEventSurface(),
                  })
                }
              >
                Открыть приложение
                <span className="landing-action__arrow" aria-hidden="true">
                  ↗
                </span>
              </a>
              <a
                className="landing-button landing-button--secondary landing-action"
                href="#how-it-works"
              >
                Посмотреть, как всё устроено
                <span className="landing-action__arrow" aria-hidden="true">
                  ↗
                </span>
              </a>
            </div>
            <p className="landing-hero__note">
              Доступно в браузере на компьютере или смартфоне <span aria-hidden="true">·</span>{' '}
              Telegram Mini App можно подключить для тренировок в зале и общения с тренером
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
                <AppLink className="landing-feature__link" to={feature.path}>
                  Подробнее <span aria-hidden="true">→</span>
                </AppLink>
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
            <p className="landing-kicker">Работает на ваших устройствах</p>
            <h2 id="landing-platforms-title">
              <span>Открывайте на компьютере или смартфоне.</span>{' '}
              <span>Продолжайте в Telegram, когда удобнее.</span>
            </h2>
            <p>
              Устанавливать отдельную программу не нужно: веб-приложение работает прямо в браузере.
              Telegram Mini App остаётся дополнительным способом открыть те же данные.
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
                <span>Веб-приложение</span>
              </div>
              <h3>Открывайте на компьютере или смартфоне</h3>
              <p>
                Программы, тренировки и прогресс доступны прямо в браузере без отдельной установки.
              </p>
            </article>

            <article className="landing-platform-card landing-platform-card--telegram">
              <div className="landing-platform-card__top">
                <span className="landing-platform-card__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="m21 4-8.2 16-3.1-7.1L3 9.8 21 4Z" />
                    <path d="m9.7 12.9 4.8-4.3" />
                  </svg>
                </span>
                <span>Дополнительная возможность</span>
              </div>
              <h3>Продолжайте в Telegram Mini App</h3>
              <p>
                Открывайте то же занятие внутри Telegram и переходите к переписке со своим тренером.
              </p>
            </article>
          </div>

          <div className="landing-platforms__sync" aria-label="Данные синхронизируются">
            <span className="landing-flow-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="M4 8h16m-3-3 3 3-3 3M20 16H4m3-3-3 3 3 3" />
              </svg>
            </span>
            <p>
              <strong>Один аккаунт и общие данные</strong>
              <span>
                Начните на одном устройстве, продолжите на другом — программа и прогресс останутся
                на месте. Для самостоятельных тренировок Telegram не нужен; общение с тренером
                происходит в Telegram.
              </span>
            </p>
          </div>
        </section>

        <section className="landing-audience" aria-label="Выберите подходящий сценарий">
          <article>
            <p className="landing-kicker">Занимаетесь самостоятельно?</p>
            <h2>Тренируйтесь по понятному плану в своём темпе</h2>
            <p>
              Выберите готовую программу или соберите свою. Выполняйте занятия и отслеживайте
              прогресс в браузере — Telegram для этого не нужен.
            </p>
            <AppLink className="landing-button landing-audience__link" to="/training">
              Узнать о тренировках
              <span className="landing-action__arrow" aria-hidden="true">
                ↗
              </span>
            </AppLink>
          </article>
          <article>
            <p className="landing-kicker">Вы тренер?</p>
            <h2>Подайте заявку и откройте кабинет тренера</h2>
            <p>
              Войдите в приложение как обычный пользователь и нажмите «Стать тренером» в профиле.
              После одобрения заявки сможете приглашать клиентов, назначать программы и следить за
              прогрессом.
            </p>
            <AppLink className="landing-button landing-audience__link" to="/for-trainers">
              Возможности для тренеров
              <span className="landing-action__arrow" aria-hidden="true">
                ↗
              </span>
            </AppLink>
          </article>
        </section>

        <section id="contact" className="landing-contact">
          <div className="landing-contact__copy">
            <p className="landing-kicker">Начните в браузере</p>
            <h2>Откройте Your Fitness Coach и выберите свой путь</h2>
            <p>
              Создайте обычный аккаунт и начните тренироваться. Если хотите вести клиентов, подайте
              заявку на роль тренера в разделе «Профиль» — писать администратору отдельно не нужно.
            </p>
          </div>
          <div className="landing-contact__actions">
            <a
              className="landing-button landing-contact__primary landing-action"
              href={appUrl}
              onClick={() =>
                trackProductEvent({ name: 'landing_app_selected', surface: productEventSurface() })
              }
            >
              Перейти в веб-приложение
              <span className="landing-action__arrow" aria-hidden="true">
                ↗
              </span>
            </a>
            <a
              className="landing-button landing-button--secondary landing-contact__link landing-action"
              href="https://t.me/your_fitness_coach_bot?start=support"
              target="_blank"
              rel="noreferrer"
            >
              <strong>Задать вопрос в Telegram</strong>
              <span className="landing-action__arrow" aria-hidden="true">
                ↗
              </span>
            </a>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <a className="landing-brand" href="#top">
          <BrandLogo
            className="landing-brand__mark"
            decorative
            variant="full"
            width={36}
            height={36}
          />
          <span>Your Fitness Coach</span>
        </a>
        <p>
          <AppLink to="/training">Тренировки</AppLink> · <AppLink to="/nutrition">Питание</AppLink>{' '}
          · <AppLink to="/knowledge">База знаний</AppLink> ·{' '}
          <AppLink to="/for-trainers">Для тренеров</AppLink>
        </p>
        <span>© {new Date().getFullYear()}</span>
      </footer>
    </PublicShell>
  );
}
