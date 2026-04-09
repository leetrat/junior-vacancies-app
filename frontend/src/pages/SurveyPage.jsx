import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { submitSurvey } from '../api';
import './SurveyPage.css';

const WORK_FORMAT_OPTIONS = [
  { value: 'remote',   label: 'Удалённо' },
  { value: 'fullDay',  label: 'Полный день' },
  { value: 'flexible', label: 'Гибкий график' },
  { value: 'shift', label: 'Сменный' },
];

export default function SurveyPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const [form, setForm] = useState({
    it_experience: '',
    load_level:    '',
    corporate:     '',
    work_format:   [],
    salary_from:   '',
    salary_to:     '',
  });
  const [resumeFile, setResumeFile] = useState(null);

  function setField(key, value) {
    setForm(f => ({ ...f, [key]: value }));
  }

  function toggleFormat(val) {
    setForm(f => {
      const cur = f.work_format;
      return {
        ...f,
        work_format: cur.includes(val) ? cur.filter(v => v !== val) : [...cur, val],
      };
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.it_experience || !form.load_level || !form.corporate) {
      setError('Пожалуйста, ответьте на все вопросы опроса.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const fd = new FormData();
      fd.append('it_experience', form.it_experience);
      fd.append('load_level',    form.load_level);
      fd.append('corporate',     form.corporate);
      fd.append('salary_from',   form.salary_from);
      fd.append('salary_to',     form.salary_to);
      form.work_format.forEach(wf => fd.append('work_format', wf));
      if (resumeFile) fd.append('resume', resumeFile);

      const data = await submitSurvey(fd);
      sessionStorage.setItem('surveyResult', JSON.stringify(data));
      navigate('/clusters');
    } catch (err) {
      setError('Ошибка сервера. Попробуйте ещё раз.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <div className="main-cards-container">
          <div className="card survey-card">
            <h1 className="survey-title">📋 Опрос</h1>
            <p className="survey-subtitle">
              Это нужно, чтобы подобрать вакансии, подходящие специально для вас!
            </p>

            <form onSubmit={handleSubmit}>

              <QuestionGroup
                  label="Какой у вас опыт работы в IT сфере?"
                  name="it_experience"
                  value={form.it_experience}
                  onChange={v => setField('it_experience', v)}
                  options={[
                    {value: 'low', label: 'Низкий'},
                    {value: 'medium', label: 'Средний'},
                    {value: 'high', label: 'Высокий'},
                    {value: 'any', label: 'Неважно'},
                  ]}
              />

              <QuestionGroup
                  label="Какой ваш предпочитаемый уровень нагрузки?"
                  name="load_level"
                  value={form.load_level}
                  onChange={v => setField('load_level', v)}
                  options={[
                    {value: 'low', label: 'Низкий'},
                    {value: 'medium', label: 'Умеренный'},
                    {value: 'high', label: 'Интенсивный'},
                    {value: 'any', label: 'Неважно'},
                  ]}
              />

              <div className="question-group">
                <p className="question-label">Какой формат работы вам удобен?</p>
                <div className="options-row">
                  {WORK_FORMAT_OPTIONS.map(o => (
                      <label key={o.value} className={`radio-option ${
                          form.work_format.includes(o.value) ? 'active' : ''
                      }`}>
                        <input
                            type="checkbox"
                            checked={form.work_format.includes(o.value)}
                            onChange={() => toggleFormat(o.value)}/>
                        {o.label}
                      </label>
                  ))}
                </div>
              </div>

              <QuestionGroup
                  label="Насколько вам близка корпоративная этика?"
                  name="corporate"
                  value={form.corporate}
                  onChange={v => setField('corporate', v)}
                  options={[
                    {value: 'close', label: 'Близка'},
                    {value: 'far', label: 'Далека'},
                    {value: 'any', label: 'Неважно'},
                  ]}
              />

              <div className="question-group">
                <p className="question-label">Загрузить резюме (необязательно)</p>
                <p className="question-hint">PDF или DOCX — поможет точнее определить кластер</p>
                <label className="file-upload">
                  <input
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={e => setResumeFile(e.target.files[0] || null)}
                  />
                  <span className="file-btn">
                  {resumeFile ? `📄 ${resumeFile.name}` : 'Выбрать файл'}
                </span>
                </label>
              </div>

              {error && <p className="error-msg">{error}</p>}

              <button className="btn-primary submit-btn" type="submit" disabled={loading}>
                {loading ? 'Загрузка…' : 'Перейти к выбору кластеров →'}
              </button>
            </form>
          </div>
          <div>
          <div className="content-card">
            <div className="card-header">
              <h3>💡 Как это работает</h3>
            </div>
            <div className="card-container">
              <div className="card-container2">
                <div className="card-number">1
                </div>
                <div>
                  <div className="card-name">Заполните анкету</div>
                  <div className="card-description">Ответьте на вопросы о ваших предпочтениях</div>
                </div>
              </div>
              <div className="card-container2">
                <div className="card-number">2
                </div>
                <div>
                  <div className="card-name">AI анализирует</div>
                  <div className="card-description">Алгоритм подбирает подходящие вакансии</div>
                </div>
              </div>
              <div className="card-container2">
                <div className="card-number">3
                </div>
                <div>
                  <div className="card-name">Получите подборку</div>
                  <div className="card-description">Вакансии, идеально подходящие именно вам</div>
                </div>
              </div>
            </div>
          </div>
          <div className="cards-grid">
            <div className="stat-card">
              <div className="card-icon2">🎯</div>
              <div className="card-value">~1000</div>
              <div className="card-label">Вакансий в базе</div>
              <div className="card-change positive">↗ +12 на этой неделе</div>
            </div>
            <div className="stat-card">
              <div className="card-icon3">⚡</div>
              <div className="card-value">2 мин</div>
              <div className="card-label">Среднее время</div>
              <div className="card-change positive">↗ Быстрее 78%</div>
            </div>
          </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function QuestionGroup({label, name, value, onChange, options}) {
  return (
      <div className="question-group">
        <p className="question-label">{label}</p>
        <div className="options-row">
          {options.map(o => (
              <label
                  key={o.value}
                  className={`radio-option ${value === o.value ? 'active' : ''}`}
              >
                <input
                    type="radio"
                    name={name}
                    value={o.value}
                    checked={value === o.value}
                    onChange={() => onChange(o.value)}
                />
                {o.label}
              </label>
          ))}
        </div>
      </div>
  );
}
