export interface BarcodeScannerSession {
  strategy: 'native' | 'zxing';
  stop: () => void;
}

interface DetectedBarcode {
  format?: string;
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

function expandUpceToUpca(value: string): string {
  if (!/^[01]\d{7}$/.test(value)) return value;

  const numberSystem = value[0];
  const payload = value.slice(1, 7);
  const checkDigit = value[7];
  const expansionRule = payload[5];
  let manufacturer: string;
  let product: string;

  if (expansionRule === '0' || expansionRule === '1' || expansionRule === '2') {
    manufacturer = `${payload.slice(0, 2)}${expansionRule}00`;
    product = `00${payload.slice(2, 5)}`;
  } else if (expansionRule === '3') {
    manufacturer = `${payload.slice(0, 3)}00`;
    product = `000${payload.slice(3, 5)}`;
  } else if (expansionRule === '4') {
    manufacturer = `${payload.slice(0, 4)}0`;
    product = `0000${payload[4]}`;
  } else {
    manufacturer = payload.slice(0, 5);
    product = `0000${expansionRule}`;
  }

  return `${numberSystem}${manufacturer}${product}${checkDigit}`;
}

function normalizeDetectedBarcode(value: string, isUpce: boolean): string {
  return isUpce ? expandUpceToUpca(value) : value;
}

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
      const supportsRetailContract = NATIVE_FORMATS.every((format) => supported.includes(format));
      if (supportsRetailContract) detector = new Detector({ formats: NATIVE_FORMATS });
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
            const value = normalizeDetectedBarcode(
              candidate.rawValue,
              candidate.format === 'upc_e',
            );
            if (onDetected(value)) {
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
    const value = normalizeDetectedBarcode(
      result.getText(),
      result.getBarcodeFormat() === BarcodeFormat.UPC_E,
    );
    if (onDetected(value)) stop();
  });
  if (!active) controls.stop();
  return { strategy: 'zxing', stop };
}
