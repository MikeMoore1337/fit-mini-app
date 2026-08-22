import { describe, expect, it } from 'vitest';
import { createTelegramMock } from '../../../helpers/telegramMock';

describe('Telegram component test harness', () => {
  it('dispatches one BackButton click through onClick and the equivalent WebApp event', () => {
    const controller = createTelegramMock();
    let onClickCalls = 0;
    let onEventCalls = 0;
    const onClick = () => {
      onClickCalls += 1;
    };
    const onEvent = () => {
      onEventCalls += 1;
    };
    controller.webApp.BackButton?.onClick(onClick);
    controller.webApp.onEvent?.('backButtonClicked', onEvent);

    controller.clickBack();

    expect(onClickCalls).toBe(1);
    expect(onEventCalls).toBe(1);
    controller.webApp.BackButton?.offClick(onClick);
    controller.webApp.offEvent?.('backButtonClicked', onEvent);
    controller.clickBack();
    expect(onClickCalls).toBe(1);
    expect(onEventCalls).toBe(1);
  });
});
