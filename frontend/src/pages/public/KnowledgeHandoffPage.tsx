import { useEffect } from 'react';
import { AppLink, useNavigation } from '../../shared/navigation/router';
import { appUrlForHostname, publicUrlForHostname } from '../../shared/navigation/appUrl';
import { PublicWebLink } from '../../shared/navigation/PublicWebLink';
import { isTelegramLaunch } from '../../shared/telegram/launch';
import { Card, LoadingState } from '../../shared/ui/common';

export default function KnowledgeHandoffPage({ articlePath }: { articlePath: string }) {
  const { navigate } = useNavigation();
  const isMiniApp =
    Boolean(window.Telegram?.WebApp?.initData?.trim()) || isTelegramLaunch(window.location);
  const appUrl = appUrlForHostname(window.location.hostname);

  const returnToApplication = () => {
    if (appUrl.startsWith('/')) {
      navigate(appUrl, true);
    } else {
      window.location.replace(appUrl);
    }
  };

  useEffect(() => {
    if (isMiniApp) return;
    const href = publicUrlForHostname(window.location.hostname, articlePath);

    if (href.startsWith('/')) {
      navigate(href, true);
    } else {
      window.location.replace(href);
    }
  }, [articlePath, isMiniApp, navigate]);

  if (!isMiniApp) {
    return (
      <main className="container standalone-page standalone-page--design-v2">
        <LoadingState label="Открываем материал на сайте…" />
      </main>
    );
  }

  return (
    <main className="container standalone-page standalone-page--design-v2 knowledge-handoff-page">
      <Card collapsible={false} title="Продолжить чтение на сайте">
        <p className="muted">
          Длинные материалы открываются во внешнем браузере, а быстрые действия остаются в Mini App.
        </p>
        <div className="toolbar wrap knowledge-handoff__actions">
          <PublicWebLink
            className="button-link knowledge-handoff__primary"
            path={articlePath}
            onTelegramOpen={returnToApplication}
          >
            Открыть материал на сайте
          </PublicWebLink>
          {appUrl.startsWith('/') ? (
            <AppLink className="button-link secondary-link" to={appUrl}>
              Вернуться в приложение
            </AppLink>
          ) : (
            <a className="button-link secondary-link" href={appUrl}>
              Вернуться в приложение
            </a>
          )}
        </div>
      </Card>
    </main>
  );
}
