import { useEffect, useRef, useState, type ImgHTMLAttributes } from 'react';
import { productEventSurface, trackProductEvent } from '../../shared/analytics/productEvents';
import {
  appUrlForHostname,
  demoUrlForHostname,
  loginUrlForHostname,
} from '../../shared/navigation/appUrl';
import { AppLink } from '../../shared/navigation/router';
import { applyRouteMetadata } from '../../shared/seo/metadata';
import { BrandLockup, BrandLogo } from '../../shared/ui/BrandLogo';
import { Icon, type IconName } from '../../shared/ui/Icon';
import { PublicShell } from '../../shared/ui/PublicShell';
import { useWebTheme } from '../../shared/useWebTheme';
import { EnergyFlow } from './EnergyFlow';
import './landing.css';

export {
  appUrlForHostname,
  demoUrlForHostname,
  loginUrlForHostname,
} from '../../shared/navigation/appUrl';

type DemoScenario = 'self_training' | 'nutrition' | 'trainer';

const coreFeatures: ReadonlyArray<{
  icon: IconName;
  index: string;
  label: string;
  title: string;
  text: string;
  href: string;
  linkLabel: string;
}> = [
  {
    icon: 'week-strength',
    index: '01',
    label: 'Сегодня и тренировка',
    title: 'Сначала — одно понятное действие.',
    text: 'Экран «Сегодня» собирает недельный контекст и ближайшую тренировку. Во время занятия остаются вес, повторы, выполненные подходы и отдых — без ручного подсчёта.',
    href: '/training',
    linkLabel: 'Как устроены тренировки',
  },
  {
    icon: 'nav-nutrition',
    index: '02',
    label: 'Питание',
    title: 'Ориентир рядом с фактическими записями.',
    text: 'Дневник различает заполненный, неполный и пропущенный день. Калории и КБЖУ остаются ориентирами, а отсутствие записи не превращается в ноль.',
    href: '/nutrition',
    linkLabel: 'Подробнее о питании',
  },
  {
    icon: 'nav-progress',
    index: '03',
    label: 'Прогресс',
    title: 'Выводы только там, где хватает данных.',
    text: 'Тренировки, питание и измерения показаны по периодам. Если записей мало, интерфейс объяснит ограничение вместо сильного вывода из одной точки.',
    href: '/progress',
    linkLabel: 'Как читать прогресс',
  },
];

const workflow: ReadonlyArray<{
  icon: IconName;
  number: string;
  title: string;
  text: string;
}> = [
  {
    icon: 'nav-profile',
    number: '01',
    title: 'Настройте профиль',
    text: 'Цель, опыт и исходные параметры задают первый понятный ориентир.',
  },
  {
    icon: 'week-strength',
    number: '02',
    title: 'Действуйте сегодня',
    text: 'Откройте тренировку или дневник питания и фиксируйте факты по ходу дня.',
  },
  {
    icon: 'nav-progress',
    number: '03',
    title: 'Сверяйтесь с динамикой',
    text: 'Смотрите подтверждённые результаты сами или разбирайте их вместе с тренером.',
  },
];

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
  const [failedSrc, setFailedSrc] = useState<string>();
  const [loadedSrc, setLoadedSrc] = useState<string>();
  const failed = failedSrc === imageProps.src;
  const loaded = loadedSrc === imageProps.src;

  return (
    <span className={`landing-product-image ${loaded ? 'is-loaded' : ''} ${className}`.trim()}>
      <span className="landing-product-image__fallback">{fallback}</span>
      {!failed && (
        <img
          {...imageProps}
          className={loaded ? 'is-loaded' : ''}
          decoding="async"
          onLoad={() => setLoadedSrc(imageProps.src)}
          onError={() => setFailedSrc(imageProps.src)}
        />
      )}
    </span>
  );
}

function AthleteVisual() {
  const [failedStem, setFailedStem] = useState<string>();
  const [loadedStem, setLoadedStem] = useState<string>();
  const assetStem = '/assets/marketing/landing-athlete-deadlift-cutout';
  const failed = failedStem === assetStem;
  const loaded = loadedStem === assetStem;

  return (
    <span className={`landing-athlete-image ${loaded ? 'is-loaded' : ''}`}>
      <span className="landing-athlete-image__fallback">
        Силовая тренировка остаётся контекстом страницы. Продукт и основные действия доступны без
        изображения.
      </span>
      {!failed && (
        <picture>
          <source
            type="image/webp"
            srcSet={`${assetStem}-640.webp 640w, ${assetStem}-960.webp 960w, ${assetStem}-1280.webp 1280w`}
            sizes="(max-width: 680px) calc(100vw - 28px), (max-width: 980px) calc(100vw - 48px), 760px"
          />
          <img
            src={`${assetStem}-1280.webp`}
            alt="Атлет выполняет контролируемую классическую становую тягу со штангой"
            width={1280}
            height={1171}
            loading="eager"
            fetchPriority="high"
            decoding="async"
            className={loaded ? 'is-loaded' : ''}
            onLoad={() => setLoadedStem(assetStem)}
            onError={() => setFailedStem(assetStem)}
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
          <EnergyFlow className="landing-energy-path" />
          <div className="landing-hero__copy">
            <p className="landing-kicker">План на сегодня. Результат — в динамике.</p>
            <h1 id="landing-title">
              Знайте, что делать <span>сегодня.</span>
            </h1>
            <p className="landing-hero__lead">
              Когда программа настроена, экран «Сегодня» показывает ближайшее запланированное
              действие — не нужно каждый раз решать, что делать дальше. Тренировки, дневник питания
              и честная картина прогресса — в одном продукте для самостоятельной работы или занятий
              с тренером.
            </p>
            <div className="landing-hero__actions">
              <a className="landing-button" href={appUrl} onClick={trackAppSelection}>
                Открыть приложение <Icon name="arrow-right" size={20} />
              </a>
              <a
                className="landing-button landing-button--secondary"
                href={cabinetScenarioUrl(demoUrl, 'self_training')}
                onClick={trackDemoSelection}
              >
                Попробовать демо <Icon name="arrow-right" size={20} />
              </a>
            </div>
            <p className="landing-hero__platform-note">
              <Icon name="web-app" size={16} /> Web и Telegram Mini App · один аккаунт и общие
              данные
            </p>
          </div>

          <div
            className="landing-hero-scene"
            role="group"
            aria-label="Силовая тренировка и актуальный интерфейс YFC"
          >
            <figure className="landing-athlete-frame">
              <AthleteVisual />
            </figure>
            <figure className="landing-hero-device">
              <span className="landing-hero-device__label">
                Актуальный интерфейс · подготовленные данные
              </span>
              <ProductScreenshot
                src={`/assets/product/landing-workout-mobile-${colorScheme}.png`}
                alt="Актуальный экран Сегодня и текущей силовой тренировки в Mobile Web"
                width={390}
                height={844}
                loading="eager"
                fetchPriority="high"
                fallback="Экран Сегодня временно недоступен. Откройте демо, чтобы посмотреть продукт."
              />
              <figcaption>
                <strong>Реальный интерфейс</strong>
                Подготовленные данные без информации реальных пользователей
              </figcaption>
            </figure>
            <div className="landing-hero-signals" aria-label="В одном профиле">
              {coreFeatures.map((feature) => (
                <span key={feature.label}>
                  <Icon name={feature.icon} size={20} /> {feature.label}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section id="product" className="landing-core" aria-labelledby="product-title">
          <div className="landing-core__intro">
            <header>
              <p className="landing-kicker">Продукт в действии</p>
              <h2 id="product-title">Не каталог функций, а связный день.</h2>
              <p>
                Экран «Сегодня» связывает запланированное действие с фактом выполнения и последующей
                динамикой.
              </p>
              <div className="landing-core__self">
                <p className="landing-kicker">Занимаетесь самостоятельно?</p>
                <h3>
                  План на сегодня, тренировки, питание и отслеживание прогресса — в одном месте.
                </h3>
                <p>
                  Выберите готовую программу или соберите свою. Выполняйте занятия и отслеживайте
                  фактическую динамику в браузере — Telegram для этого не нужен.
                </p>
                <AppLink className="landing-core__self-link" to="/training">
                  Начать с тренировок <Icon name="arrow-right" size={20} />
                </AppLink>
              </div>
            </header>
            <div className="landing-core__proof" aria-label="Актуальные Web и Mobile Web экраны">
              <figure className="landing-core__desktop">
                <ProductScreenshot
                  src={`/assets/product/landing-today-desktop-${colorScheme}.png`}
                  alt="Актуальный экран Сегодня в desktop Web"
                  width={1440}
                  height={900}
                  loading="lazy"
                  fallback="Desktop proof временно недоступен."
                />
              </figure>
              <figure className="landing-core__mobile">
                <ProductScreenshot
                  src={`/assets/product/landing-today-mobile-${colorScheme}.png`}
                  alt="Актуальный экран Сегодня в Mobile Web"
                  width={390}
                  height={844}
                  loading="lazy"
                  fallback="Mobile proof временно недоступен."
                />
              </figure>
              <div className="landing-core__context">
                <BrandLogo decorative surface={colorScheme} variant="mark" width={38} height={38} />
                <span>Один профиль</span>
                <strong>План → факт → динамика</strong>
              </div>
            </div>
          </div>

          <div className="landing-core__features" aria-label="Тренировки, питание и прогресс">
            {coreFeatures.map((feature) => (
              <article key={feature.index}>
                <div className="landing-core__feature-label">
                  <span>{feature.index}</span>
                  <Icon name={feature.icon} size={20} />
                  <small>{feature.label}</small>
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
                <AppLink to={feature.href}>{feature.linkLabel}</AppLink>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-trainer" aria-labelledby="trainer-title">
          <div className="landing-trainer__copy">
            <p className="landing-kicker">04 · Работа с тренером</p>
            <h2 id="trainer-title">У каждого клиента — видимый контекст.</h2>
            <p>
              Тренер включает режим из профиля, приглашает клиента, назначает программу, видит
              выполненную работу и оставляет комментарии к конкретным тренировкам. CRM, платежи и
              расписание бизнеса остаются за пределами продукта.
            </p>
            <AppLink className="landing-button" to="/for-trainers">
              Посмотреть кабинет тренера <Icon name="arrow-right" size={20} />
            </AppLink>
          </div>
          <figure className="landing-trainer__proof">
            <ProductScreenshot
              src={`/assets/product/landing-trainer-desktop-${colorScheme}.png`}
              alt="Актуальный кабинет тренера с подготовленными данными клиента"
              width={1280}
              height={972}
              loading="lazy"
              fallback="Экран кабинета тренера временно недоступен."
            />
          </figure>
        </section>

        <section id="demo" className="landing-start" aria-labelledby="start-title">
          <header>
            <p className="landing-kicker">Как это работает</p>
            <h2 id="start-title">От настройки — к повторяемому ритму.</h2>
          </header>
          <ol className="landing-start__steps">
            {workflow.map((step) => (
              <li key={step.number}>
                <span aria-hidden="true">
                  <Icon name={step.icon} />
                </span>
                <small>{step.number}</small>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </li>
            ))}
          </ol>
          <div className="landing-start__demo">
            <div>
              <p className="landing-kicker">Демо без регистрации</p>
              <h3>Три сценария. Никаких реальных данных.</h3>
              <p>
                Изменения живут только в отдельной подготовленной сессии и не переносятся в аккаунт.
                Приглашения, уведомления и действия с реальными пользователями заблокированы.
              </p>
            </div>
            <nav aria-label="Демо-сценарии">
              {demoScenarios.map((scenario, index) => (
                <a
                  key={scenario.value}
                  href={cabinetScenarioUrl(demoUrl, scenario.value)}
                  onClick={trackDemoSelection}
                >
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <div>
                    <small>{scenario.eyebrow}</small>
                    <strong>{scenario.title}</strong>
                    <p>{scenario.text}</p>
                  </div>
                  <Icon name="arrow-right" size={20} />
                </a>
              ))}
            </nav>
          </div>
        </section>

        <section id="faq" className="landing-assurance" aria-labelledby="faq-title">
          <div className="landing-assurance__platform">
            <div className="landing-continuity__copy">
              <p className="landing-kicker">Один продукт на двух поверхностях</p>
              <h2 id="continuity-title">
                Web для полного контекста. Telegram — для быстрых действий.
              </h2>
              <p>
                Полный продукт на компьютере и смартфоне без отдельной установки. Telegram Mini App
                не является отдельным приложением или библиотекой статей: интерфейс, тема и основные
                данные общие с Mobile Web. Тренировка, питание, краткий прогресс и переход к общению
                с тренером.
              </p>
            </div>
            <div className="landing-continuity__rail" aria-label="Один аккаунт и общие данные">
              <span>
                <Icon name="web-app" /> Web
              </span>
              <Icon name="sync" size={24} />
              <strong>Один аккаунт · общие данные</strong>
              <Icon name="sync" size={24} />
              <span>
                <Icon name="mini-app" /> Telegram Mini App
              </span>
            </div>
          </div>
          <header>
            <p className="landing-kicker">Честные ограничения</p>
            <h2 id="faq-title">Перед тем как начать.</h2>
          </header>
          <div className="landing-assurance__grid">
            <div className="landing-faq-list">
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
            <div className="landing-assurance__details">
              <details>
                <summary>
                  <span>
                    <small>Разобраться до действия</small>
                    <strong>Короткий путь к проверяемому объяснению.</strong>
                  </span>
                  <Icon name="plus" size={20} />
                </summary>
                <div>
                  <p>
                    Публичные материалы помогают понять тренировочный план, ориентиры питания и
                    ограничения прогресса. Они не заменяют индивидуальную медицинскую помощь.
                  </p>
                  <nav aria-label="Материалы о продукте и тренировках">
                    <AppLink to="/training">Тренировки и программы</AppLink>
                    <AppLink to="/nutrition">Питание и КБЖУ</AppLink>
                    <AppLink to="/progress">Прогресс и измерения</AppLink>
                    <AppLink to="/knowledge">База знаний</AppLink>
                  </nav>
                </div>
              </details>
              <details id="privacy">
                <summary>
                  <span>
                    <small>Приватность без входа</small>
                    <strong>Ваши данные остаются под вашим управлением.</strong>
                  </span>
                  <Icon name="plus" size={20} />
                </summary>
                <div>
                  <p>
                    До регистрации можно понять, какие данные использует продукт и какие действия с
                    ними доступны. Вход нужен только для управления конкретным аккаунтом.
                  </p>
                  <ul>
                    <li>
                      <strong>Только данные продукта.</strong> Профиль, тренировки, питание и
                      прогресс сохраняются после входа и используются для работы функций Your
                      Fitness Coach.
                    </li>
                    <li>
                      <strong>Демо изолировано.</strong> Подготовленные демо-данные не относятся к
                      реальным пользователям и не становятся данными вашего аккаунта.
                    </li>
                    <li>
                      <strong>Доступны контроль и удаление.</strong> После входа в профиле можно
                      экспортировать данные, отвязать способы входа или удалить аккаунт.
                    </li>
                  </ul>
                </div>
              </details>
            </div>
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
            <a className="landing-button" href={appUrl} onClick={trackAppSelection}>
              Открыть приложение <Icon name="arrow-right" size={20} />
            </a>
            <a
              className="landing-button landing-button--secondary"
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
          <a className="landing-brand" href="#top" aria-label="Your Fitness Coach — на главную">
            <BrandLockup className="landing-footer__lockup" markClassName="landing-brand__mark" />
          </a>
          <p>Тренировки, питание и прогресс — самостоятельно или вместе с тренером.</p>
        </div>
        <nav aria-label="Ссылки в подвале">
          <AppLink to="/training">Тренировки</AppLink>
          <AppLink to="/nutrition">Питание</AppLink>
          <AppLink to="/knowledge">База знаний</AppLink>
          <a href="#demo">Условия демо</a>
          <a href="#faq">Вопросы</a>
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
