# Amendment to existing Task 110 - Custom avatar

**Не использовать этот файл вместо существующей Task 110. Добавить пункты в её scope/acceptance.**

## Dependency

Task 110 должна выполняться после Task 122 либо на уже интегрированном Profile/AppShell layout Task 122.

## Required identity layout

- Desktop account block внизу слева: avatar слева; имя пользователя и тип клиента/роль справа.
- Если такой AppShell block уже существует, переиспользовать его - не создавать дубль.
- Avatar также видим в Profile identity area.
- Mobile/TMA используют адаптированный compact layout без буквального переноса desktop sidebar.

## Fallback order

Canonical fallback:

```text
custom avatar -> provider avatar/photo_url -> emoji/default avatar
```

Не терять provider avatar после добавления custom upload.

## Existing Task 110 behavior сохранить

- upload;
- replace;
- delete;
- privacy/safe file handling;
- export/delete-account behavior, если уже входит в 110;
- validation MIME/type/size/dimensions согласно текущему security contract.

## Additional acceptance

- [ ] Custom avatar отображается и в AppShell account block, и в Profile.
- [ ] Desktop layout = avatar left, name/client type right.
- [ ] Fallback `custom -> provider -> emoji/default` покрыт tests.
- [ ] Delete custom avatar корректно возвращает provider/default fallback.
- [ ] Mobile/TMA/Desktop и light/dark проверены.
