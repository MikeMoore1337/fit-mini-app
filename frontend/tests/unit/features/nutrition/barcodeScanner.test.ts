import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { startBarcodeScanner } from '../../../../src/features/nutrition/barcodeScanner';

const fallback = vi.hoisted(() => ({
  callback: undefined as
    | ((result?: { getBarcodeFormat: () => number; getText: () => string }, error?: Error) => void)
    | undefined,
  stop: vi.fn(),
}));

vi.mock('@zxing/browser', () => ({
  BarcodeFormat: { EAN_13: 1, EAN_8: 2, UPC_A: 3, UPC_E: 4, ITF: 5 },
  BrowserMultiFormatReader: class {
    possibleFormats: number[] = [];

    decodeFromStream(
      _stream: MediaStream,
      _video: HTMLVideoElement,
      callback: (
        result?: { getBarcodeFormat: () => number; getText: () => string },
        error?: Error,
      ) => void,
    ) {
      fallback.callback = callback;
      return Promise.resolve({ stop: fallback.stop });
    }
  },
}));

describe('barcode scanner strategy', () => {
  const video = document.createElement('video');
  const stream = {} as MediaStream;

  beforeEach(() => {
    fallback.callback = undefined;
    fallback.stop.mockReset();
    vi.stubGlobal('requestAnimationFrame', vi.fn());
    vi.stubGlobal('cancelAnimationFrame', vi.fn());
    Object.defineProperty(globalThis, 'BarcodeDetector', { configurable: true, value: undefined });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    Object.defineProperty(globalThis, 'BarcodeDetector', { configurable: true, value: undefined });
  });

  it('uses native BarcodeDetector as the fast path and accepts only a caller-approved value', async () => {
    let scheduled: FrameRequestCallback | undefined;
    vi.stubGlobal(
      'requestAnimationFrame',
      vi.fn((callback: FrameRequestCallback) => {
        scheduled = callback;
        return 17;
      }),
    );
    const detect = vi
      .fn()
      .mockResolvedValue([
        { rawValue: 'not-a-gtin' },
        { rawValue: '4006381333931' },
        { rawValue: '3017620422003' },
      ]);
    Object.defineProperty(globalThis, 'BarcodeDetector', {
      configurable: true,
      value: class {
        detect = detect;
      },
    });
    const onDetected = vi.fn((value: string) => value === '4006381333931');

    const session = await startBarcodeScanner({
      stream,
      video,
      onDetected,
      onFatalError: vi.fn(),
    });
    scheduled?.(0);
    await vi.waitFor(() => expect(onDetected).toHaveBeenCalledTimes(2));

    expect(session.strategy).toBe('native');
    expect(detect).toHaveBeenCalledWith(video);
    expect(cancelAnimationFrame).toHaveBeenCalledWith(17);
  });

  it('expands native UPC-E results to the equivalent UPC-A value', async () => {
    let scheduled: FrameRequestCallback | undefined;
    vi.stubGlobal(
      'requestAnimationFrame',
      vi.fn((callback: FrameRequestCallback) => {
        scheduled = callback;
        return 18;
      }),
    );
    Object.defineProperty(globalThis, 'BarcodeDetector', {
      configurable: true,
      value: class {
        detect = vi.fn().mockResolvedValue([{ format: 'upc_e', rawValue: '01234565' }]);
      },
    });
    const onDetected = vi.fn(() => true);

    const session = await startBarcodeScanner({
      stream,
      video,
      onDetected,
      onFatalError: vi.fn(),
    });
    scheduled?.(0);
    await vi.waitFor(() => expect(onDetected).toHaveBeenCalledOnce());

    expect(session.strategy).toBe('native');
    expect(onDetected).toHaveBeenCalledWith('012345000065');
  });

  it('lazy-loads the local ZXing path without BarcodeDetector and retries decode misses', async () => {
    const onDetected = vi.fn(() => true);
    const onFatalError = vi.fn();
    const session = await startBarcodeScanner({ stream, video, onDetected, onFatalError });

    expect(session.strategy).toBe('zxing');
    fallback.callback?.(undefined, new Error('not found'));
    expect(fallback.stop).not.toHaveBeenCalled();
    fallback.callback?.({ getBarcodeFormat: () => 1, getText: () => '3017620422003' });
    fallback.callback?.({ getBarcodeFormat: () => 1, getText: () => '4006381333931' });

    expect(onDetected).toHaveBeenCalledOnce();
    expect(onDetected).toHaveBeenCalledWith('3017620422003');
    expect(fallback.stop).toHaveBeenCalledOnce();
    expect(onFatalError).not.toHaveBeenCalled();
  });

  it('expands UPC-E results to the equivalent UPC-A value before validation', async () => {
    const onDetected = vi.fn(() => true);
    const session = await startBarcodeScanner({
      stream,
      video,
      onDetected,
      onFatalError: vi.fn(),
    });

    fallback.callback?.({ getBarcodeFormat: () => 4, getText: () => '01234565' });

    expect(session.strategy).toBe('zxing');
    expect(onDetected).toHaveBeenCalledWith('012345000065');
  });

  it('falls back to ZXing when a partial native implementation rejects retail formats', async () => {
    Object.defineProperty(globalThis, 'BarcodeDetector', {
      configurable: true,
      value: class {
        static getSupportedFormats() {
          return Promise.resolve(['qr_code']);
        }
      },
    });

    const session = await startBarcodeScanner({
      stream,
      video,
      onDetected: vi.fn(() => true),
      onFatalError: vi.fn(),
    });

    expect(session.strategy).toBe('zxing');
  });
});
