import { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { ExternalFood, Food, FoodBarcodeLookup } from '../../shared/api/types';
import { Button, Field, Input, LoadingState } from '../../shared/ui/common';
import { isValidGtin } from './FoodEditor';

interface DetectedBarcode {
  rawValue: string;
}

interface BarcodeDetectorLike {
  detect(source: HTMLVideoElement): Promise<DetectedBarcode[]>;
}

type BarcodeDetectorConstructor = new (options?: { formats?: string[] }) => BarcodeDetectorLike;

const TOUCH_CAMERA_QUERY = '(hover: none) and (pointer: coarse)';

function providerMessage(status: FoodBarcodeLookup['provider_status']): string | null {
  if (status === 'disabled')
    return 'Внешний каталог не подключён. Локальный поиск и свои продукты доступны.';
  if (status === 'rate_limited')
    return 'Внешний каталог временно занят. Можно добавить продукт вручную.';
  if (status === 'unavailable')
    return 'Внешний каталог временно недоступен. Можно добавить продукт вручную.';
  return null;
}

function ExternalBarcodeResult({ food }: { food: ExternalFood }) {
  return (
    <article className="nutrition-external-result">
      <div>
        <span className="eyebrow">Внешний каталог</span>
        <h3>{food.name}</h3>
        <p>
          {food.brand || 'Без бренда'} ·{' '}
          {Number(food.energy_kcal_per_100g).toLocaleString('ru-RU', { maximumFractionDigits: 1 })}{' '}
          ккал / 100 г
        </p>
      </div>
      <p>
        Эта карточка доступна только для сверки. Чтобы сохранить данные в личный каталог, создайте
        свой продукт и проверьте значения на упаковке.
      </p>
      <div className="nutrition-external-result__links">
        <a href={food.source.source_url} target="_blank" rel="noreferrer">
          Открыть источник
        </a>
        <a href={food.source.license_url} target="_blank" rel="noreferrer">
          {food.source.attribution} · {food.source.license}
        </a>
      </div>
    </article>
  );
}

export function BarcodeLookup({
  onCreate,
  onSelect,
}: {
  onCreate: (barcode: string) => void;
  onSelect: (food: Food) => void;
}) {
  const [barcode, setBarcode] = useState('');
  const [validationError, setValidationError] = useState('');
  const [cameraError, setCameraError] = useState('');
  const [scanning, setScanning] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameRef = useRef<number | null>(null);
  const stoppedRef = useRef(false);
  const Detector = (
    globalThis as typeof globalThis & { BarcodeDetector?: BarcodeDetectorConstructor }
  ).BarcodeDetector;
  const cameraSupported = Boolean(Detector && navigator.mediaDevices?.getUserMedia);
  const [touchCameraSurface, setTouchCameraSurface] = useState(
    () => window.matchMedia?.(TOUCH_CAMERA_QUERY).matches ?? false,
  );
  const cameraFirst = cameraSupported && touchCameraSurface;

  useEffect(() => {
    const media = window.matchMedia?.(TOUCH_CAMERA_QUERY);
    if (!media) return;
    const sync = () => setTouchCameraSurface(media.matches);
    sync();
    media.addEventListener('change', sync);
    return () => media.removeEventListener('change', sync);
  }, []);

  const stopCamera = () => {
    stoppedRef.current = true;
    if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setScanning(false);
  };
  useEffect(() => stopCamera, []);

  const lookup = useMutation({
    mutationFn: (value: string) =>
      api<FoodBarcodeLookup>(`/api/v1/nutrition/foods/barcode/${value}`),
  });
  const submitBarcode = (value: string) => {
    const normalized = value.replace(/\s+/g, '');
    if (!isValidGtin(normalized)) {
      setValidationError('Проверьте цифры штрихкода GTIN-8, UPC-A, EAN-13 или GTIN-14.');
      return;
    }
    setValidationError('');
    setBarcode(normalized);
    lookup.mutate(normalized);
  };
  const startCamera = async () => {
    if (!Detector || !navigator.mediaDevices?.getUserMedia) {
      setCameraError(
        'Сканирование камерой не поддерживается в этом браузере. Введите код вручную.',
      );
      return;
    }
    setCameraError('');
    stoppedRef.current = false;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      });
      streamRef.current = stream;
      if (!videoRef.current) return stopCamera();
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      setScanning(true);
      const detector = new Detector({ formats: ['ean_13', 'ean_8', 'upc_a', 'itf'] });
      const scan = async () => {
        if (stoppedRef.current || !videoRef.current) return;
        try {
          const results = await detector.detect(videoRef.current);
          const found = results.find((item) => isValidGtin(item.rawValue));
          if (found) {
            stopCamera();
            submitBarcode(found.rawValue);
            return;
          }
        } catch {
          setCameraError(
            'Не удалось распознать код. Наведите камеру на штрихкод или введите его вручную.',
          );
          stopCamera();
          return;
        }
        frameRef.current = window.requestAnimationFrame(() => void scan());
      };
      frameRef.current = window.requestAnimationFrame(() => void scan());
    } catch (error) {
      stopCamera();
      const name = error instanceof DOMException ? error.name : '';
      setCameraError(
        name === 'NotAllowedError' || name === 'SecurityError'
          ? 'Доступ к камере запрещён. Разрешите его в настройках браузера или введите код вручную.'
          : name === 'NotFoundError' || name === 'OverconstrainedError'
            ? 'Камера не найдена. Введите штрихкод вручную.'
            : 'Не удалось открыть камеру. Введите штрихкод вручную.',
      );
    }
  };
  const result = lookup.data;
  const providerFallback = result ? providerMessage(result.provider_status) : null;

  return (
    <div className="nutrition-barcode">
      <div className="nutrition-tools-heading">
        <div>
          <h3>Поиск по штрихкоду</h3>
          <p>Сначала проверим личный и локальный каталоги, затем — бесплатный внешний источник.</p>
        </div>
      </div>
      {cameraFirst && (
        <div className="nutrition-camera">
          <video
            ref={videoRef}
            muted
            playsInline
            className={scanning ? 'is-active' : ''}
            aria-label="Изображение с камеры"
          />
          {scanning ? (
            <Button type="button" variant="secondary" fullWidth onClick={stopCamera}>
              Остановить камеру
            </Button>
          ) : (
            <Button type="button" fullWidth onClick={() => void startCamera()}>
              Сканировать камерой
            </Button>
          )}
          {cameraError && (
            <p className="nutrition-form-error" role="alert">
              {cameraError}
            </p>
          )}
        </div>
      )}
      <form
        className="nutrition-barcode__manual"
        onSubmit={(event) => {
          event.preventDefault();
          submitBarcode(barcode);
        }}
      >
        {cameraFirst && <p className="nutrition-barcode__manual-title">Или введите код вручную</p>}
        <Field
          label="Штрихкод"
          labelFor="nutrition-barcode-input"
          error={validationError}
          hint="8, 12, 13 или 14 цифр"
        >
          <div className="nutrition-barcode__input-row">
            <Input
              id="nutrition-barcode-input"
              inputMode="numeric"
              autoComplete="off"
              maxLength={14}
              value={barcode}
              onChange={(event) => {
                lookup.reset();
                setValidationError('');
                setBarcode(event.target.value.replace(/\D/g, ''));
              }}
              placeholder="3017620422003"
            />
            <Button
              className="nutrition-barcode__manual-submit"
              type="submit"
              variant={cameraFirst ? 'secondary' : 'primary'}
              disabled={lookup.isPending}
            >
              {lookup.isPending ? 'Ищем…' : 'Найти'}
            </Button>
          </div>
        </Field>
      </form>
      {touchCameraSurface && !cameraSupported && (
        <p className="nutrition-camera-unavailable">
          Сканирование камерой недоступно — введите цифры со штрихкода вручную.
        </p>
      )}
      {lookup.isPending && <LoadingState label="Проверяем каталоги…" />}
      {lookup.error && (
        <div className="nutrition-provider-fallback" role="alert">
          <strong>Не удалось выполнить поиск.</strong>
          <span>
            Дневник и локальные продукты продолжают работать. Попробуйте снова или создайте свой
            продукт.
          </span>
        </div>
      )}
      {result?.status === 'found' && result.local_item && (
        <div className="nutrition-barcode__found">
          <strong>{result.local_item.name}</strong>
          <span>
            {result.local_item.brand || 'Локальный каталог'} ·{' '}
            {Number(result.local_item.energy_kcal_per_100g).toLocaleString('ru-RU', {
              maximumFractionDigits: 1,
            })}{' '}
            ккал / 100 г
          </span>
          <Button type="button" onClick={() => onSelect(result.local_item!)}>
            Выбрать продукт
          </Button>
        </div>
      )}
      {result?.status === 'found' && result.external_item && (
        <>
          <ExternalBarcodeResult food={result.external_item} />
          <Button type="button" variant="secondary" onClick={() => onCreate(result.barcode)}>
            Создать свой продукт
          </Button>
        </>
      )}
      {result?.status === 'not_found' && (
        <div className="nutrition-provider-fallback">
          <strong>Продукт не найден</strong>
          <span>
            {providerFallback || 'Проверьте код или добавьте продукт по данным с упаковки.'}
          </span>
          <Button type="button" variant="secondary" onClick={() => onCreate(result.barcode)}>
            Создать свой продукт
          </Button>
        </div>
      )}
    </div>
  );
}
