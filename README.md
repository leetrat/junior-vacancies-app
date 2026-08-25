# Подбор вакансий — веб-приложение

## Возможности

- Рекомендация вакансий в карьерном направлении по опросу
- Анализ вакансий с выявлением редфлагов
- AI-анализ резюме
- Фильтрация вакансий по навыкам и параметрам

---

## Архитектура

- Frontend: React
- Backend: Flask
- API: REST
- AI: локальная LLM (llama.cpp)
- Данные вакансий: hh.ru API

---

## Шаг 1 — Загрузка дополнительных данных

https://colab.research.google.com/drive/1Kzx8EFPhv7Cwul7vdZ8JVbmkAphXhLLT?usp=sharing

В Google Colab нажмите ```Выполнить все``` и дождитесь загрузки файлов:

```
df_for_clasters.csv
top_companies.csv
junior_it_skills.json
sbert_model.zip
```

https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/blob/main/Phi-3.5-mini-instruct-Q4_K_M.gguf

Скачайте модель ```Phi-3.5-mini-instruct-GGUF```. Переименуйте его в ```model.gguf```

Сохраните все все файлы из Google Colab в `backend/data/`. Распакуйте туда же `sbert_model.zip.

Также рекомендовано создать файл `hf_token.txt`, где хранится ваш токен от Hugging Face.

---

## Шаг 2 — Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Бэкенд запустится на `http://localhost:5000`.

Если по какой-то причине модуль llama не устанавливается, пропишите:

```pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir```

или

```pip install llama-cpp-python --prefer-binary```

Если не получилось, установите Visual Studio Build Tools и установите Desctop development with C++. Потом опять попробуйте предыдущие команды.

---

## Шаг 3 — Frontend

```bash
cd frontend
npm install
npm start
```

Фронтенд запустится на `http://localhost:3000`.  
Запросы на `/api/*` автоматически проксируются на `localhost:5000` (настроено в `package.json`).

---

## API эндпоинты

| Метод | URL                    | Описание                                                                                                   |
| ----- | ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| POST  | `/api/survey`          | Принимает ответы опроса + (опционально) резюме, возвращает рекомендованный кластер и список всех кластеров |
| GET   | `/api/clusters`        | Получить список всех карьерных кластеров                                                                   |
| GET   | `/api/clusters/<id>`   | Получить информацию о конкретном кластере                                                                  |
| POST  | `/api/result`          | Получить вакансии по выбранным кластерам с учётом фильтров                                                 |
| POST  | `/api/analyze_vacancy` | Анализ вакансии по ссылке (hh.ru): зарплата, навыки, редфлаги                                              |
| POST  | `/api/analyze_resume`  | Анализ резюме с помощью LLM (выделение навыков, рекомендации)                                              |
| GET   | `/api/career_fields`   | Получить список карьерных направлений (для фильтров/опроса)                                                |


