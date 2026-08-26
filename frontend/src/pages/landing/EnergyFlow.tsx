import { useId } from 'react';

type EnergyFlowProps = {
  className?: string;
};

const desktopFilaments = [
  {
    className:
      'energy-flow__filament energy-flow__filament--primary energy-flow__filament--primary-a',
    d: 'M-92 548 C96 554 221 519 360 526 C493 533 568 501 642 454 C722 404 767 331 849 299 C921 271 967 348 1031 361 C1091 373 1137 308 1216 278 C1320 237 1410 274 1490 245',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--primary energy-flow__filament--primary-b',
    d: 'M-78 572 C112 579 239 551 378 541 C516 531 608 506 690 460 C778 410 822 385 901 372 C980 358 1013 425 1081 416 C1143 407 1182 346 1251 320 C1350 284 1437 320 1492 292',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-a',
    d: 'M-104 501 C62 510 168 533 301 511 C432 489 529 472 637 421 C744 370 793 296 881 282 C966 268 1014 329 1085 319 C1154 309 1191 265 1265 248 C1354 228 1422 262 1496 222',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-b',
    d: 'M-81 594 C75 582 181 557 314 558 C454 559 564 532 681 489 C796 447 865 421 946 430 C1033 440 1078 473 1154 416 C1219 367 1288 326 1370 329 C1422 331 1460 325 1498 311',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-c',
    d: 'M-96 551 C54 564 159 552 286 540 C416 527 545 523 665 473 C779 425 826 367 911 339 C997 311 1036 384 1100 382 C1168 379 1204 317 1276 292 C1361 263 1424 294 1491 273',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-d',
    d: 'M-67 515 C99 539 219 508 350 517 C483 526 565 493 672 444 C775 397 813 339 895 310 C978 281 1020 346 1082 348 C1142 351 1188 285 1260 261 C1355 229 1424 270 1494 238',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-e',
    d: 'M-88 612 C82 603 203 586 339 568 C475 550 579 558 700 519 C814 482 874 458 958 468 C1046 479 1085 442 1157 392 C1233 339 1301 329 1374 353 C1425 370 1462 351 1500 339',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-f',
    d: 'M-110 536 C44 545 148 519 279 528 C426 538 519 515 634 466 C742 420 784 362 870 321 C957 279 1016 304 1089 299 C1160 294 1205 246 1278 226 C1363 204 1434 243 1498 211',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-g',
    d: 'M-75 567 C79 555 189 569 319 546 C459 521 554 526 674 478 C785 434 844 392 929 373 C1014 354 1046 417 1111 404 C1174 392 1211 337 1282 314 C1367 286 1432 324 1496 302',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-h',
    d: 'M-91 482 C62 511 177 487 304 488 C436 489 531 470 640 429 C744 390 790 326 873 293 C959 258 1012 271 1082 285 C1150 299 1192 247 1264 231 C1351 211 1427 246 1492 218',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-i',
    d: 'M-108 626 C52 606 156 608 294 589 C432 570 550 578 672 536 C785 497 855 470 944 480 C1032 489 1073 451 1149 422 C1225 393 1282 343 1354 368 C1414 389 1458 373 1501 356',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-j',
    d: 'M-84 531 C71 519 178 542 321 524 C458 506 564 509 682 462 C794 417 839 356 922 320 C1005 284 1046 349 1110 346 C1175 343 1215 290 1285 270 C1371 245 1435 283 1497 258',
  },
] as const;

const mobileFilaments = [
  {
    className:
      'energy-flow__filament energy-flow__filament--primary energy-flow__filament--primary-a',
    d: 'M-30 301 C50 251 102 260 161 320 C208 368 231 430 280 380 C329 330 350 260 400 290 C430 309 445 299 460 270',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--primary energy-flow__filament--primary-b',
    d: 'M-30 361 C60 340 102 301 170 340 C218 368 240 309 285 320 C331 331 341 410 390 380 C421 361 441 330 460 340',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-a',
    d: 'M-30 250 C59 281 101 241 165 270 C219 295 231 360 280 350 C321 342 340 300 380 290 C420 280 440 311 460 300',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-b',
    d: 'M-30 410 C60 390 109 430 175 390 C226 359 245 430 295 420 C340 410 360 350 400 360 C430 368 445 390 460 370',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-c',
    d: 'M-30 315 C60 300 120 355 180 320 C230 291 250 380 295 370 C340 360 360 281 405 310 C431 327 445 320 460 295',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-d',
    d: 'M-30 455 C50 440 101 390 170 420 C220 442 250 390 300 400 C350 410 365 450 410 420 C434 404 448 392 462 380',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-e',
    d: 'M-30 285 C50 325 105 275 170 305 C215 325 235 270 280 285 C330 300 350 360 395 345 C425 335 443 312 460 320',
  },
  {
    className:
      'energy-flow__filament energy-flow__filament--support energy-flow__filament--support-f',
    d: 'M-30 380 C55 352 105 375 168 355 C220 338 244 405 292 392 C338 380 354 315 398 330 C430 341 446 365 461 345',
  },
] as const;

export function EnergyFlow({ className = '' }: EnergyFlowProps) {
  const id = useId().replace(/:/g, '');
  const gradientId = `energy-flow-gradient-${id}`;
  const fadeMaskId = `energy-flow-fade-${id}`;
  const maskGradientId = `energy-flow-mask-gradient-${id}`;
  const ambientBlurId = `energy-flow-ambient-blur-${id}`;
  const coreBlurId = `energy-flow-core-blur-${id}`;

  return (
    <div className={`energy-flow ${className}`.trim()} aria-hidden="true">
      <svg viewBox="0 0 1320 660" preserveAspectRatio="none" focusable="false">
        <defs>
          <linearGradient
            id={gradientId}
            x1="-90"
            y1="0"
            x2="1490"
            y2="0"
            gradientUnits="userSpaceOnUse"
          >
            <stop className="energy-flow__stop energy-flow__stop--start" offset="0" />
            <stop className="energy-flow__stop energy-flow__stop--deep" offset="0.14" />
            <stop className="energy-flow__stop energy-flow__stop--muted" offset="0.43" />
            <stop className="energy-flow__stop energy-flow__stop--bright" offset="0.7" />
            <stop className="energy-flow__stop energy-flow__stop--tail" offset="0.9" />
            <stop className="energy-flow__stop energy-flow__stop--end" offset="1" />
          </linearGradient>
          <linearGradient
            id={maskGradientId}
            x1="-90"
            y1="0"
            x2="1490"
            y2="0"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0" stopColor="black" />
            <stop offset="0.08" stopColor="white" />
            <stop offset="0.91" stopColor="white" />
            <stop offset="1" stopColor="black" />
          </linearGradient>
          <mask
            id={fadeMaskId}
            x="-120"
            y="190"
            width="1660"
            height="440"
            maskUnits="userSpaceOnUse"
          >
            <rect x="-120" y="190" width="1660" height="440" fill={`url(#${maskGradientId})`} />
          </mask>
          <filter
            id={ambientBlurId}
            x="-18%"
            y="-80%"
            width="136%"
            height="260%"
            colorInterpolationFilters="sRGB"
          >
            <feGaussianBlur stdDeviation="14" />
          </filter>
          <filter
            id={coreBlurId}
            x="-10%"
            y="-45%"
            width="120%"
            height="190%"
            colorInterpolationFilters="sRGB"
          >
            <feGaussianBlur stdDeviation="4.5" />
          </filter>
        </defs>

        <g className="energy-flow__volume" mask={`url(#${fadeMaskId})`}>
          <g className="energy-flow__scene energy-flow__scene--desktop">
            <path
              className="energy-flow__ambient"
              d="M-105 556 C76 568 184 541 326 539 C474 536 574 511 674 466 C779 418 824 357 908 333 C991 309 1031 382 1098 377 C1163 372 1206 309 1278 282 C1364 250 1431 287 1494 259"
              fill="none"
              stroke={`url(#${gradientId})`}
              filter={`url(#${ambientBlurId})`}
            />
            <path
              className="energy-flow__glow energy-flow__glow--a"
              d={desktopFilaments[0].d}
              fill="none"
              stroke={`url(#${gradientId})`}
              filter={`url(#${coreBlurId})`}
            />
            <path
              className="energy-flow__glow energy-flow__glow--b"
              d={desktopFilaments[1].d}
              fill="none"
              stroke={`url(#${gradientId})`}
              filter={`url(#${coreBlurId})`}
            />
            {desktopFilaments.map((filament, index) => (
              <path
                key={filament.className}
                className={filament.className}
                data-flow-index={index + 1}
                d={filament.d}
                fill="none"
                pathLength="100"
                stroke={`url(#${gradientId})`}
              />
            ))}
          </g>
          <g
            className="energy-flow__scene energy-flow__scene--mobile"
            transform="scale(3.069767 1)"
          >
            <path
              className="energy-flow__ambient"
              d="M-30 348 C55 324 108 318 170 350 C220 376 243 394 290 379 C337 364 355 326 398 337 C429 345 445 345 460 326"
              fill="none"
              stroke={`url(#${gradientId})`}
              filter={`url(#${ambientBlurId})`}
            />
            <path
              className="energy-flow__glow energy-flow__glow--a"
              d={mobileFilaments[0].d}
              fill="none"
              stroke={`url(#${gradientId})`}
              filter={`url(#${coreBlurId})`}
            />
            {mobileFilaments.map((filament, index) => (
              <path
                key={filament.className}
                className={filament.className}
                data-flow-index={index + 1}
                d={filament.d}
                fill="none"
                pathLength="100"
                stroke={`url(#${gradientId})`}
              />
            ))}
          </g>
        </g>
      </svg>
    </div>
  );
}
