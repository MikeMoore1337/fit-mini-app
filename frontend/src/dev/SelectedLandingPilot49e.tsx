type SelectedLandingPilot49eProps = {
  appUrl: string;
};

export default function SelectedLandingPilot49e({ appUrl }: SelectedLandingPilot49eProps) {
  return (
    <main id="landing-content" className="pilot49e-landing" tabIndex={-1}>
      <section className="pilot49e-landing-hero" aria-labelledby="landing-title">
        <div className="pilot49e-landing-hero__copy">
          <p className="pilot49e-kicker">План на сегодня. Результат — в динамике.</p>
          <h1 id="landing-title">Знайте, что делать сегодня.</h1>
          <p className="pilot49e-landing-hero__lead">
            Программа тренировок, дневник питания и честная картина прогресса — в одном продукте для
            самостоятельной работы или занятий с тренером.
          </p>
          <div className="pilot49e-landing-hero__actions">
            <a className="landing-button" href={appUrl}>
              Открыть приложение
            </a>
            <a className="landing-button landing-button--secondary" href="#how-it-works">
              Как всё устроено
            </a>
          </div>
          <p className="pilot49e-landing-hero__note">
            В браузере и Telegram Mini App · один профиль и одна система
          </p>
        </div>

        <article
          className="pilot49e-landing-proof"
          aria-label="Пример текущего состояния тренировки"
        >
          <div className="pilot49e-landing-proof__top">
            <span>Сегодня · 22 августа</span>
            <strong>В процессе</strong>
          </div>
          <h2>Силовая база</h2>
          <p>Жим штанги лёжа · подход 2 из 3</p>
          <div className="pilot49e-landing-proof__track" aria-label="Выполнено два подхода из трёх">
            <i />
            <i />
            <i />
          </div>
          <dl className="pilot49e-landing-proof__values">
            <div>
              <dt>Вес</dt>
              <dd>22,5 кг</dd>
            </div>
            <div>
              <dt>Повторы</dt>
              <dd>10</dd>
            </div>
            <div>
              <dt>Отдых</dt>
              <dd>01:24</dd>
            </div>
          </dl>
        </article>

        <div className="pilot49e-landing-mobile-evidence">
          <span>Последние 30 дней</span>
          <strong>10 из 12 тренировок</strong>
          <small>Факты и ограничения остаются видимыми.</small>
        </div>
      </section>

      <section id="how-it-works" className="pilot49e-story pilot49e-story--today">
        <div className="pilot49e-story__heading">
          <span aria-hidden="true">01</span>
          <p className="pilot49e-kicker">Следующий шаг</p>
          <h2>Не обзор ради обзора — одно главное действие.</h2>
        </div>
        <div className="pilot49e-story__current">
          <strong>Сегодня</strong>
          <span>Продолжить тренировку</span>
          <small>0 из 3 подходов</small>
        </div>
        <p>
          Today сохраняет контекст тренировок, питания и прогресса, но не заставляет считывать всё
          сразу.
        </p>
      </section>

      <section id="for-who" className="pilot49e-story pilot49e-story--progress">
        <div className="pilot49e-progress-proof" aria-label="Выполнение плана за последние 30 дней">
          <span>Выполнение плана</span>
          <strong>10 из 12</strong>
          <div aria-hidden="true">
            <i />
          </div>
          <small>83% · за последние 30 дней</small>
        </div>
        <div className="pilot49e-story__heading">
          <span aria-hidden="true">02</span>
          <p className="pilot49e-kicker">Честный прогресс</p>
          <h2>Факты, сравнение с собой и понятные ограничения.</h2>
          <p>Без «идеального тела», магических score и выводов из нескольких записей.</p>
        </div>
      </section>
    </main>
  );
}
