# Исправление обработки ошибок на Frontend

## Проблема

При попытке изменить пароль на такой же (или других ошибках), frontend показывал техническое сообщение:
```
Request failed with status code 400
```

Вместо человекопонятного русского сообщения от API.

## Причина

Frontend искал сообщение об ошибке в поле `detail` (старый формат FastAPI):
```javascript
if (error.response?.data?.detail) {
  errorMessage = error.response.data.detail;
}
```

Но после реализации русских сообщений, API стал возвращать новый формат:
```json
{
  "error": true,
  "message": "Новый пароль должен отличаться от текущего",
  "status_code": 400
}
```

## Решение

Обновлен файл `frontend/src/services/api.js`:

1. **Добавлена поддержка нового формата** (поле `message`)
2. **Сохранена обратная совместимость** (поле `detail`)
3. **Добавлена обработка ошибок валидации** (массив `errors`)

### Код исправления:

```javascript
// Новый формат ошибок (русские сообщения)
if (error.response?.data?.message) {
  errorMessage = error.response.data.message;

  // Если есть дополнительные ошибки валидации
  if (error.response.data.errors && Array.isArray(error.response.data.errors)) {
    const validationErrors = error.response.data.errors
      .map(err => err.message || err.field)
      .join('; ');
    errorMessage = validationErrors || errorMessage;
  }
}
// Старый формат с detail (для совместимости)
else if (error.response?.data?.detail) {
  // ... старая логика
}
```

## Результат

Теперь при любых ошибках frontend показывает **русские сообщения**:

### 1. Попытка установить тот же пароль
**Ответ API:**
```json
{
  "error": true,
  "message": "Новый пароль должен отличаться от текущего",
  "status_code": 400
}
```
**Отображается на frontend:** "Новый пароль должен отличаться от текущего"

### 2. Неверный текущий пароль
**Ответ API:**
```json
{
  "error": true,
  "message": "Неверный текущий пароль",
  "status_code": 400
}
```
**Отображается на frontend:** "Неверный текущий пароль"

### 3. Неверный email или пароль при входе
**Ответ API:**
```json
{
  "error": true,
  "message": "Неверный email или пароль",
  "status_code": 401
}
```
**Отображается на frontend:** "Неверный email или пароль"

### 4. Ошибки валидации (422)
**Ответ API:**
```json
{
  "error": true,
  "message": "Обнаружено ошибок валидации: 4",
  "errors": [
    {
      "field": "Email",
      "message": "Email: Неверный формат данных",
      "type": "value_error"
    },
    {
      "field": "Пароль",
      "message": "Пароль: Минимальная длина 6 символов",
      "type": "string_too_short"
    }
  ],
  "status_code": 422
}
```
**Отображается на frontend:** "Email: Неверный формат данных; Пароль: Минимальная длина 6 символов"

## Тестирование

### Через API (curl):
```bash
# Получить токен
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Попытаться установить тот же пароль
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"test1234","new_password":"test1234"}'

# Результат: {"error": true, "message": "Новый пароль должен отличаться от текущего", ...}
```

### Через UI:
1. Открыть http://localhost:3000/profile
2. Попытаться изменить пароль на такой же
3. **Ожидаемый результат:** Alert с текстом "Новый пароль должен отличаться от текущего"

## Преимущества

1. ✅ **Понятные сообщения** - пользователь видит что именно не так
2. ✅ **Русский язык** - все сообщения локализованы
3. ✅ **Детальная информация** - при ошибках валидации показываются все проблемы
4. ✅ **Обратная совместимость** - старый формат тоже поддерживается
5. ✅ **Единый формат** - все ошибки обрабатываются одинаково

## Файлы изменены

- `frontend/src/services/api.js` - обновлен response interceptor для поддержки нового формата ошибок
