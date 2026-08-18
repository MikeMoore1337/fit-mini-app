# Exercise guide media foundation

## Current inventory

The application ships exercise guide media locally and has no runtime CDN, paid API, or
remote media dependency. The checked-in inventory contains 158 covered exercise slugs and
307 JPEG assets (19,596,935 bytes):

- 149 exercises have two reviewed static phases (`start` and `active`);
- 9 cardio exercises have one locally created composition showing both phases;
- no guide slug is missing its expected media;
- intrinsic dimensions range from portrait to landscape and are recorded per asset instead
  of forcing a cropping ratio.

The two provenance groups are `free-exercise-db` under the Unlicense and locally created
Your Fitness Coach cardio illustrations. `backend/assets/exercise-guides/NOTICE.md` and
`manifest.json` preserve their source and license status. Fitness Online assets and text are
not used.

## Format decision

The default production pattern is ordered, static phase images. It gives users simultaneous
access to the positions they need to compare, works without motion, and matches the
information present in the legal source material. Technique text always remains available.

| Candidate               | Representative result                                      | Clarity and compatibility                                                                                              | Decision                                 |
| ----------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Two static JPEG phases  | 142-145 kB total for bench press, squat, and treadmill run | Universal browser fallback; phases can be compared; current legal catalog is complete                                  | **Default**                              |
| Two static WebP phases  | 90-100 kB in the local quality-80 benchmark                | Smaller, but converting all 307 reviewed binaries would be a separate catalog-wide change                              | Not shipped in this task                 |
| Two-frame animated WebP | 91-100 kB in the same benchmark                            | Almost no size advantage over two static WebPs; a hard frame switch invents no real movement path and adds motion      | Rejected for current assets              |
| Short WebM              | Requires owned continuous footage and codec/device testing | Can show a real trajectory, but needs a poster, `preload="none"`, controls, codec fallback, and additional decode cost | Future option for reviewed owned footage |
| APNG/AVIF animation     | No useful content advantage for two JPEG keyframes         | Adds another format/fallback branch; animated AVIF has less historical support                                         | Rejected for the MVP                     |

The browser behavior assumptions follow MDN's current
[image format guide](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types),
[`img` loading guidance](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/img),
and [`video` preload/poster contract](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/video).
If continuous owned footage is added later, it must not autoplay with sound, must use a static
poster/fallback and `preload="none"`, and must remain user-controlled when
`prefers-reduced-motion: reduce` is active.

## Runtime contract

`exercise_guide_metadata.media_reference` remains the stable link introduced by the exercise
domain foundation. The local manifest owns asset-level facts; task 23 metadata remains the
API source of truth for guide provenance. `ExerciseGuide.media[]` exposes:

- `type`, `url`, static `poster`, phase, alt text, and deterministic `sort_order`;
- intrinsic `width` and `height` for reserved layout, plus `byte_size` for inventory control;
- source name/URL and license name/URL on every item.

The legacy `images[]` response is derived from the same media list for backward compatibility;
it is not a second asset registry.

The frontend requests the guide only after the user opens it. Media then uses native
`loading="lazy"`, `decoding="async"`, intrinsic dimensions, the recorded aspect ratio, and
`object-fit: contain`. A failed image request becomes an accessible reserved-size fallback;
it does not remove the text technique. Hover zoom is disabled under reduced motion.

Exercise assets are served by the existing same-origin `StaticFiles` mount with ETag and a
30-day cache plus one-day `stale-while-revalidate`. Filenames are stable rather than
content-hashed, so they intentionally are not marked `immutable`.

## Reproducible pipeline

After adding or synchronizing legal assets:

```powershell
.\.venv\Scripts\python.exe scripts\sync_exercise_guide_assets.py
.\.venv\Scripts\python.exe scripts\build_exercise_guide_media_manifest.py
.\.venv\Scripts\python.exe scripts\build_exercise_guide_media_manifest.py --check
```

The builder fails on missing or unexpected JPEG files, verifies that every image decodes,
and writes deterministic dimensions, byte sizes, phases, order, and provenance. New media
must have an explicit legal source before it is admitted to the manifest. A future real-video
pilot should be limited to a representative owned set and must pass desktop Web, iOS Safari,
Android Chrome, and Telegram WebView checks before `type` is expanded beyond `image`.
