import { useEffect, useRef, useState, type ImgHTMLAttributes } from 'react';
import { BrandLogo } from '../../shared/ui/BrandLogo';
import { PublicShell } from '../../shared/ui/PublicShell';
import { applyRouteMetadata } from '../../shared/seo/metadata';
import {
  appUrlForHostname,
  demoUrlForHostname,
  loginUrlForHostname,
} from '../../shared/navigation/appUrl';
import { AppLink } from '../../shared/navigation/router';
import { Icon } from '../../shared/ui/Icon';
import { productEventSurface, trackProductEvent } from '../../shared/analytics/productEvents';
import { useWebTheme } from '../../shared/useWebTheme';
import './landing.css';

export {
  appUrlForHostname,
  demoUrlForHostname,
  loginUrlForHostname,
} from '../../shared/navigation/appUrl';

type DemoScenario = 'self_training' | 'nutrition' | 'trainer';

const capabilities = [
  ['Тренировки', 'План на сегодня, подходы и отдых'],
  ['Питание', 'Дневник и ориентиры КБЖУ'],
  ['Прогресс', 'Факты, периоды и ограничения данных'],
  ['Тренер', 'Программы и контекст по каждому клиенту'],
] as const;

const workflow = [
  ['01', 'Настройте профиль', 'Цель, опыт и исходные параметры задают первый понятный ориентир.'],
  [
    '02',
    'Действуйте сегодня',
    'Откройте тренировку или дневник питания и фиксируйте факты по ходу дня.',
  ],
  [
    '03',
    'Сверяйтесь с динамикой',
    'Смотрите подтверждённые результаты сами или разбирайте их вместе с тренером.',
  ],
] as const;

const demoScenarios: ReadonlyArray<{
  value: DemoScenario;
  eyebrow: string;
  title: string;
  text: string;
}> = [
  {
    value: 'self_training',
    eyebrow: 'Для себя',
    title: 'Пройдите тренировку',
    text: 'Начните занятие, отметьте подходы и посмотрите, как результат становится частью прогресса.',
  },
  {
    value: 'nutrition',
    eyebrow: 'Дневник',
    title: 'Добавьте питание',
    text: 'Запишите недавний продукт и откройте дневной итог рядом с фактическими ориентирами.',
  },
  {
    value: 'trainer',
    eyebrow: 'Клиент',
    title: 'Посмотрите кабинет тренера',
    text: 'Откройте результат подготовленного клиента и сохраните контекстный комментарий.',
  },
];

const faqs = [
  {
    question: 'Telegram обязателен?',
    answer:
      'Нет. Тренировки, питание и прогресс доступны в браузере. Telegram Mini App — быстрый дополнительный вход к тем же основным сценариям и удобный переход к общению с тренером.',
  },
  {
    question: 'Что произойдёт с изменениями в демо?',
    answer:
      'Они останутся только в подготовленной демо-сессии и не перенесутся в аккаунт. После входа вы начнёте настройку чистого профиля со своими данными.',
  },
  {
    question: 'Нужно подавать заявку, чтобы стать тренером?',
    answer:
      'Нет. После входа пользователь может сразу включить режим тренера в профиле. Это добавляет кабинет клиентов, но не заменяет CRM, платежи, расписание бизнеса или мессенджер.',
  },
  {
    question: 'Приложение само меняет программу или питание?',
    answer:
      'Нет. Приложение показывает план, факты и объяснимые ориентиры. Изменения программы и целей остаются явными действиями пользователя или его тренера.',
  },
  {
    question: 'Можно ли управлять своими данными?',
    answer:
      'В профиле доступны экспорт данных, отвязка способов входа и удаление аккаунта. Данные подготовленных демо-сценариев отделены от реальных аккаунтов.',
  },
] as const;

function cabinetScenarioUrl(baseUrl: string, scenario: DemoScenario): string {
  const section =
    scenario === 'nutrition' ? 'nutrition' : scenario === 'trainer' ? 'trainer' : 'today';
  return `${baseUrl}?cabinet=1&scenario=${scenario}&section=${section}`;
}

type ProductScreenshotProps = Pick<
  ImgHTMLAttributes<HTMLImageElement>,
  'alt' | 'className' | 'fetchPriority' | 'height' | 'loading' | 'src' | 'width'
> & { fallback: string };

function ProductScreenshot({ fallback, className = '', ...imageProps }: ProductScreenshotProps) {
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);

  return (
    <span className={`landing-product-image ${className}`.trim()}>
      <span className="landing-product-image__fallback">{fallback}</span>
      {!failed && (
        <img
          {...imageProps}
          className={loaded ? 'is-loaded' : ''}
          decoding="async"
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
        />
      )}
    </span>
  );
}

function HeroScreenshot({ colorScheme }: { colorScheme: 'light' | 'dark' }) {
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const isDark = colorScheme === 'dark';

  return (
    <span className="landing-product-image landing-hero-proof__image">
      <span className="landing-product-image__fallback">
        Экран Сегодня временно недоступен. Откройте демо, чтобы посмотреть продукт.
      </span>
      {!failed && (
        <picture>
          <source
            media="(max-width: 680px)"
            srcSet={
              isDark
                ? '/assets/product/landing-workout-mobile-dark.png'
                : '/assets/product/landing-workout-mobile-light.png'
            }
          />
          <img
            src={
              isDark
                ? '/assets/product/landing-today-desktop-dark.png'
                : '/assets/product/landing-today-desktop-light.png'
            }
            alt="Экран Сегодня: недельный контекст и тренировка в приложении"
            width={isDark ? 1440 : 1280}
            height={972}
            loading="eager"
            fetchPriority="high"
            decoding="async"
            className={loaded ? 'is-loaded' : ''}
            onLoad={() => setLoaded(true)}
            onError={() => setFailed(true)}
          />
        </picture>
      )}
    </span>
  );
}

export default function LandingPage() {
  const appUrl = appUrlForHostname(window.location.hostname);
  const loginUrl = loginUrlForHostname(window.location.hostname);
  const demoUrl = demoUrlForHostname(window.location.hostname);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { colorScheme } = useWebTheme();
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const navigationRef = useRef<HTMLElement>(null);

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
      if (event.key !== 'Escape') return;
      setMobileMenuOpen(false);
      menuButtonRef.current?.focus();
    };
    const closeOnOutsidePointer = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (navigationRef.current?.contains(target) || menuButtonRef.current?.contains(target))
        return;
      setMobileMenuOpen(false);
    };

    window.addEventListener('keydown', closeOnEscape);
    window.addEventListener('pointerdown', closeOnOutsidePointer);
    return () => {
      window.removeEventListener('keydown', closeOnEscape);
      window.removeEventListener('pointerdown', closeOnOutsidePointer);
    };
  }, [mobileMenuOpen]);

  const trackAppSelection = () =>
    trackProductEvent({ name: 'landing_app_selected', surface: productEventSurface() });
  const trackDemoSelection = () =>
    trackProductEvent({ name: 'landing_demo_selected', surface: productEventSurface() });

  return (
    <PublicShell
      className="landing-page"
      homeHref="#top"
      skipTarget="landing-content"
      headerNavigation={
        <nav
          ref={navigationRef}
          id="landing-navigation"
          className={`landing-nav${mobileMenuOpen ? ' is-open' : ''}`}
          aria-label="Навигация по странице"
        >
          <a href="#product" onClick={() => setMobileMenuOpen(false)}>
            Продукт
          </a>
          <a href="#demo" onClick={() => setMobileMenuOpen(false)}>
            Демо
          </a>
          <a href="#faq" onClick={() => setMobileMenuOpen(false)}>
            Вопросы
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
            ref={menuButtonRef}
            type="button"
            className={`landing-menu-toggle${mobileMenuOpen ? ' is-open' : ''}`}
            aria-label={mobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
            aria-expanded={mobileMenuOpen}
            aria-controls="landing-navigation"
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            <Icon name={mobileMenuOpen ? 'close' : 'menu'} />
          </button>
        </>
      }
    >
      <main id="landing-content" tabIndex={-1}>
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-hero__copy">
            <p className="landing-kicker">План на сегодня. Результат — в динамике.</p>
            <h1 id="landing-title">Знайте, что делать сегодня.</h1>
            <p className="landing-hero__lead">
              Тренировки, дневник питания и честная картина прогресса — в одном продукте для
              самостоятельной работы или занятий с тренером.
            </p>
            <div className="landing-hero__primary">
              <a
                className="landing-button landing-action"
                href={appUrl}
                onClick={trackAppSelection}
              >
                Открыть приложение
                <Icon name="arrow-right" size={20} />
              </a>
              <p>Web и Telegram Mini App · один аккаунт и общие данные</p>
            </div>
          </div>

          <figure className="landing-hero-proof" aria-labelledby="landing-proof-caption">
            <div className="landing-hero-proof__viewport">
              <HeroScreenshot colorScheme={colorScheme} />
            </div>
            <figcaption id="landing-proof-caption">
              <span>Реальный интерфейс</span>
              Подготовленные данные без информации реальных пользователей
            </figcaption>
          </figure>

          <div className="landing-hero__continuation">
            <a
              className="landing-button landing-button--secondary landing-action"
              href={cabinetScenarioUrl(demoUrl, 'self_training')}
              onClick={trackDemoSelection}
            >
              Попробовать демо
              <Icon name="arrow-right" size={20} />
            </a>
          </div>
        </section>

        <section className="landing-capabilities" aria-label="Основные возможности">
          {capabilities.map(([title, text]) => (
            <div key={title}>
              <strong>{title}</strong>
              <span>{text}</span>
            </div>
          ))}
        </section>

        <section id="product" className="landing-showcase" aria-labelledby="product-title">
          <header className="landing-section-heading">
            <p className="landing-kicker">Продукт в действии</p>
            <h2 id="product-title">Не каталог функций, а связный день.</h2>
            <p>
              Начните с текущего действия, зафиксируйте питание и тренировку, затем смотрите
              динамику сами или вместе с тренером.
            </p>
          </header>

          <article className="landing-showcase-chapter landing-showcase-chapter--today">
            <div className="landing-showcase-copy">
              <span className="landing-index">01 · Сегодня и тренировка</span>
              <h3>Сначала — одно понятное действие.</h3>
              <p>
                Экран «Сегодня» собирает недельный контекст и ближайшую тренировку. Во время занятия
                остаются вес, повторы, выполненные подходы и отдых — без ручного подсчёта.
              </p>
              <AppLink to="/training">Как устроены тренировки</AppLink>
            </div>
            <div className="landing-proof-duet" aria-label="Web и mobile интерфейсы тренировки">
              <figure className="landing-proof-frame landing-proof-frame--wide">
                <ProductScreenshot
                  src="/assets/product/landing-today-desktop-light.png"
                  alt="Экран Сегодня в desktop Web"
                  width={1280}
                  height={972}
                  loading="lazy"
                  fallback="Desktop proof временно недоступен."
                />
                <figcaption>Desktop Web · Light</figcaption>
              </figure>
              <figure className="landing-proof-frame landing-proof-frame--phone">
                <ProductScreenshot
                  src="/assets/product/landing-workout-mobile-dark.png"
                  alt="Экран тренировки в Mobile Web"
                  width={390}
                  height={844}
                  loading="lazy"
                  fallback="Mobile proof временно недоступен."
                />
                <figcaption>Mobile Web · Dark</figcaption>
              </figure>
            </div>
          </article>

          <div className="landing-showcase-pair">
            <article className="landing-showcase-compact">
              <div className="landing-showcase-copy">
                <span className="landing-index">02 · Питание</span>
                <h3>Ориентир рядом с фактическими записями.</h3>
                <p>
                  Дневник различает заполненный, неполный и пропущенный день. Калории и КБЖУ
                  остаются ориентирами, а отсутствие записи не превращается в ноль.
                </p>
                <AppLink to="/nutrition">Подробнее о питании</AppLink>
              </div>
              <figure className="landing-proof-frame landing-proof-frame--landscape">
                <ProductScreenshot
                  src="/assets/product/landing-nutrition-desktop-light.png"
                  alt="Дневник питания с подготовленными данными"
                  width={1280}
                  height={972}
                  loading="lazy"
                  fallback="Экран питания временно недоступен."
                />
                <figcaption>Демо-кабинет · подготовленные данные</figcaption>
              </figure>
            </article>

            <article className="landing-showcase-compact landing-showcase-compact--progress">
              <div className="landing-showcase-copy">
                <span className="landing-index">03 · Прогресс</span>
                <h3>Выводы только там, где хватает данных.</h3>
                <p>
                  Тренировки, питание и измерения показаны по периодам. Если записей мало, интерфейс
                  объяснит ограничение вместо сильного вывода из одной точки.
                </p>
                <AppLink to="/progress">Как читать прогресс</AppLink>
              </div>
              <figure className="landing-proof-frame landing-proof-frame--phone landing-proof-frame--progress">
                <ProductScreenshot
                  src="/assets/product/landing-progress-mobile-light.png"
                  alt="Прогресс в мобильном демо-кабинете"
                  width={430}
                  height={932}
                  loading="lazy"
                  fallback="Экран прогресса временно недоступен."
                />
                <figcaption>Mobile Web · достаточность данных</figcaption>
              </figure>
            </article>
          </div>

          <article className="landing-showcase-chapter landing-showcase-chapter--trainer">
            <div className="landing-showcase-copy">
              <span className="landing-index">04 · Работа с тренером</span>
              <h3>У каждого клиента — видимый контекст.</h3>
              <p>
                Тренер приглашает клиента, назначает программу, видит выполненную работу и оставляет
                комментарий к конкретной тренировке. Режим включается сразу из профиля.
              </p>
              <AppLink to="/for-trainers">Возможности тренера</AppLink>
            </div>
            <figure className="landing-proof-frame landing-proof-frame--trainer">
              <ProductScreenshot
                src="/assets/product/landing-trainer-desktop-light.png"
                alt="Кабинет тренера с результатом подготовленного демо-клиента"
                width={1280}
                height={972}
                loading="lazy"
                fallback="Экран кабинета тренера временно недоступен."
              />
              <figcaption>Демо тренера · данные не относятся к реальному человеку</figcaption>
            </figure>
          </article>
        </section>

        <section id="how-it-works" className="landing-workflow" aria-labelledby="workflow-title">
          <header className="landing-section-heading">
            <p className="landing-kicker">Как это работает</p>
            <h2 id="workflow-title">От настройки — к повторяемому ритму.</h2>
          </header>
          <ol>
            {workflow.map(([number, title, text]) => (
              <li key={number}>
                <span>{number}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section
          className="landing-audience"
          aria-label="Сценарии самостоятельной работы и тренера"
        >
          <article>
            <p className="landing-kicker">Занимаетесь самостоятельно?</p>
            <h2>Держите план, питание и прогресс в одной системе.</h2>
            <p>
              Выберите готовую программу или соберите свою. Выполняйте занятия и отслеживайте
              фактическую динамику в браузере — Telegram для этого не нужен.
            </p>
            <AppLink className="landing-button" to="/training">
              Начать с тренировок
            </AppLink>
          </article>
          <article>
            <p className="landing-kicker">Вы тренер?</p>
            <h2>Замените таблицы на контекст по каждому клиенту.</h2>
            <p>
              Включите режим тренера сразу после входа, приглашайте клиентов, назначайте программы и
              разбирайте подтверждённые результаты. CRM, платежи и расписание бизнеса остаются за
              пределами продукта.
            </p>
            <AppLink className="landing-button" to="/for-trainers">
              Посмотреть кабинет тренера
            </AppLink>
          </article>
        </section>

        <section id="demo" className="landing-demo" aria-labelledby="demo-title">
          <header className="landing-section-heading landing-section-heading--split">
            <div>
              <p className="landing-kicker">Демо без регистрации</p>
              <h2 id="demo-title">Три сценария. Никаких реальных данных.</h2>
            </div>
            <p>
              Изменения живут только в отдельной подготовленной сессии и не переносятся в аккаунт.
              Приглашения, уведомления и действия с реальными пользователями заблокированы.
            </p>
          </header>
          <div className="landing-demo-list">
            {demoScenarios.map((scenario, index) => (
              <a
                key={scenario.value}
                href={cabinetScenarioUrl(demoUrl, scenario.value)}
                onClick={trackDemoSelection}
              >
                <span>{String(index + 1).padStart(2, '0')}</span>
                <div>
                  <small>{scenario.eyebrow}</small>
                  <h3>{scenario.title}</h3>
                  <p>{scenario.text}</p>
                </div>
                <Icon name="arrow-right" size={20} />
              </a>
            ))}
          </div>
        </section>

        <section className="landing-platforms" aria-labelledby="platforms-title">
          <div>
            <p className="landing-kicker">Один продукт на двух поверхностях</p>
            <h2 id="platforms-title">
              Web для полного контекста. Telegram — для быстрых действий.
            </h2>
          </div>
          <div className="landing-platforms__facts">
            <article>
              <span aria-hidden="true">
                <Icon name="web-app" />
              </span>
              <h3>Браузер</h3>
              <p>Полный продукт на компьютере и смартфоне без отдельной установки.</p>
            </article>
            <article>
              <span aria-hidden="true">
                <Icon name="mini-app" />
              </span>
              <h3>Telegram Mini App</h3>
              <p>Тренировка, питание, краткий прогресс и переход к общению с тренером.</p>
            </article>
          </div>
          <p className="landing-platforms__boundary">
            Telegram Mini App не является отдельным приложением или библиотекой статей: интерфейс,
            тема и основные данные общие с Mobile Web.
          </p>
        </section>

        <section className="landing-knowledge" aria-labelledby="knowledge-title">
          <header className="landing-section-heading">
            <p className="landing-kicker">Разобраться до действия</p>
            <h2 id="knowledge-title">Короткий путь к проверяемому объяснению.</h2>
            <p>
              Публичные материалы помогают понять тренировочный план, ориентиры питания и
              ограничения прогресса. Они не заменяют индивидуальную медицинскую помощь.
            </p>
          </header>
          <nav aria-label="Материалы о продукте и тренировках">
            <AppLink to="/training">
              Тренировки и программы <Icon name="arrow-right" size={20} />
            </AppLink>
            <AppLink to="/nutrition">
              Питание и КБЖУ <Icon name="arrow-right" size={20} />
            </AppLink>
            <AppLink to="/progress">
              Прогресс и измерения <Icon name="arrow-right" size={20} />
            </AppLink>
            <AppLink to="/knowledge">
              База знаний <Icon name="arrow-right" size={20} />
            </AppLink>
          </nav>
        </section>

        <section id="faq" className="landing-faq" aria-labelledby="faq-title">
          <header>
            <p className="landing-kicker">Честные ограничения</p>
            <h2 id="faq-title">Перед тем как начать.</h2>
          </header>
          <div>
            {faqs.map((item) => (
              <details key={item.question}>
                <summary>
                  {item.question}
                  <Icon name="plus" size={20} />
                </summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section id="privacy" className="landing-privacy" aria-labelledby="privacy-title">
          <header className="landing-section-heading">
            <p className="landing-kicker">Приватность без входа</p>
            <h2 id="privacy-title">Ваши данные остаются под вашим управлением.</h2>
            <p>
              До регистрации можно понять, какие данные использует продукт и какие действия с ними
              доступны. Вход нужен только для управления конкретным аккаунтом.
            </p>
          </header>
          <div className="landing-privacy__facts">
            <article>
              <span>01</span>
              <h3>Только данные продукта</h3>
              <p>
                Профиль, тренировки, питание и прогресс сохраняются после входа и используются для
                работы функций Your Fitness Coach.
              </p>
            </article>
            <article>
              <span>02</span>
              <h3>Демо изолировано</h3>
              <p>
                Подготовленные демо-данные не относятся к реальным пользователям и не становятся
                данными вашего аккаунта.
              </p>
            </article>
            <article>
              <span>03</span>
              <h3>Доступны контроль и удаление</h3>
              <p>
                После входа в профиле можно экспортировать данные, отвязать способы входа или
                удалить аккаунт.
              </p>
            </article>
          </div>
        </section>

        <section id="contact" className="landing-contact">
          <div>
            <p className="landing-kicker">Ваш следующий шаг</p>
            <h2>Откройте продукт и настройте чистый профиль.</h2>
            <p>
              Можно начать самостоятельно, а режим тренера включить позже — без заявки и ожидания.
            </p>
          </div>
          <div className="landing-contact__actions">
            <a className="landing-button landing-action" href={appUrl} onClick={trackAppSelection}>
              Открыть приложение <Icon name="arrow-right" size={20} />
            </a>
            <a
              className="landing-button landing-button--secondary landing-action"
              href="https://t.me/your_fitness_coach_bot?start=support"
              target="_blank"
              rel="noreferrer"
            >
              Поддержка в Telegram <Icon name="external-link" size={20} />
            </a>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer__brand">
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
          <p>Тренировки, питание и прогресс — самостоятельно или вместе с тренером.</p>
        </div>
        <nav aria-label="Ссылки в подвале">
          <AppLink to="/training">Тренировки</AppLink>
          <AppLink to="/nutrition">Питание</AppLink>
          <AppLink to="/knowledge">База знаний</AppLink>
          <a href="#demo">Условия демо</a>
          <a href="#privacy">Приватность и данные</a>
          <a
            href="https://t.me/your_fitness_coach_bot?start=support"
            target="_blank"
            rel="noreferrer"
          >
            Поддержка
          </a>
        </nav>
        <div className="landing-footer__privacy">
          <strong>Управление данными</strong>
          <p>Экспорт, отвязка способов входа и удаление аккаунта доступны в профиле.</p>
          <span>© {new Date().getFullYear()} Your Fitness Coach</span>
        </div>
      </footer>
    </PublicShell>
  );
}
