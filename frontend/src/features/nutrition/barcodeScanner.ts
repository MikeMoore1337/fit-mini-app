export interface BarcodeScannerSession {
  strategy: 'native' | 'zxing';
  stop: () => void;
}

interface DetectedBarcode {
  rawValue: string;
}

interface BarcodeDetectorLike {
  detect(source: HTMLVideoElement): Promise<DetectedBarcode[]>;
}

type BarcodeDetectorConstructor = {
  new (options?: { formats?: string[] }): BarcodeDetectorLike;
  getSupportedFormats?: () => Promise<string[]>;
};

const NATIVE_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'itf'];

function nativeDetector(): BarcodeDetectorConstructor | undefined {
  return (globalThis as typeof globalThis & { BarcodeDetector?: BarcodeDetectorConstructor })
    .BarcodeDetector;
}

export async function startBarcodeScanner({
  onDetected,
  onFatalError,
  stream,
  video,
}: {
  onDetected: (value: string) => boolean;
  onFatalError: () => void;
  stream: MediaStream;
  video: HTMLVideoElement;
}): Promise<BarcodeScannerSession> {
  const Detector = nativeDetector();
  if (Detector) {
    let detector: BarcodeDetectorLike | null = null;
    try {
      const supported = Detector.getSupportedFormats
        ? await Detector.getSupportedFormats()
        : NATIVE_FORMATS;
      const formats = NATIVE_FORMATS.filter((format) => supported.includes(format));
      if (formats.length > 0) detector = new Detector({ formats });
    } catch {
      detector = null;
    }
    if (detector) {
      let active = true;
      let frame: number | null = null;
      const stop = () => {
        active = false;
        if (frame !== null) window.cancelAnimationFrame(frame);
        frame = null;
      };
      const scan = async () => {
        if (!active) return;
        try {
          const found = await detector.detect(video);
          for (const candidate of found) {
            if (onDetected(candidate.rawValue)) {
              stop();
              return;
            }
          }
        } catch {
          stop();
          onFatalError();
          return;
        }
        frame = window.requestAnimationFrame(() => void scan());
      };
      frame = window.requestAnimationFrame(() => void scan());
      return { strategy: 'native', stop };
    }
  }

  const { BarcodeFormat, BrowserMultiFormatReader } = await import('@zxing/browser');
  const reader = new BrowserMultiFormatReader(undefined, {
    delayBetweenScanAttempts: 120,
    delayBetweenScanSuccess: 500,
  });
  reader.possibleFormats = [
    BarcodeFormat.EAN_13,
    BarcodeFormat.EAN_8,
    BarcodeFormat.UPC_A,
    BarcodeFormat.UPC_E,
    BarcodeFormat.ITF,
  ];
  let active = true;
  let controls: { stop: () => void } | null = null;
  const stop = () => {
    active = false;
    controls?.stop();
  };
  controls = await reader.decodeFromStream(stream, video, (result) => {
    if (!active || !result) return;
    if (onDetected(result.getText())) stop();
  });
  if (!active) controls.stop();
  return { strategy: 'zxing', stop };
}
