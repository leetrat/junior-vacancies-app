import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { analyzeResume } from '../api';
import axios from 'axios';
import './ResumePage.css';

export default function ResumePage() {
  const navigate = useNavigate();
  const [careerField,   setCareerField]   = useState('');
  const [resumeFile,    setResumeFile]    = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState('');
  const [careerFields,  setCareerFields]  = useState([]);

  useEffect(() => {
    axios.get('/api/career_fields')
      .then(r => setCareerFields(r.data))
      .catch(() => setCareerFields([
        'Python-разработчик', 'Java-разработчик', 'Frontend-разработчик',
        'Аналитик данных', 'DevOps-инженер', 'Тестировщик',
        'Android-разработчик', 'iOS-разработчик',
      ]));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!careerField) { setError('Выберите специализацию.'); return; }
    if (!resumeFile)  { setError('Загрузите файл резюме.'); return; }
    setError('');
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('career_field', careerField);
      fd.append('resume', resumeFile);
      const data = await analyzeResume(fd);
      sessionStorage.setItem('resumeResult', JSON.stringify(data));
      navigate('/resume/result');
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка при анализе. Попробуйте ещё раз.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="card tool-card">
          <h1 className="page-title">Анализ резюме</h1>
          <p className="page-subtitle">
            Загрузите резюме в формате PDF или DOCX — мы оценим ваш уровень,
            выделим сильные стороны и дадим рекомендации на основе AI-анализа.
          </p>

          <form onSubmit={handleSubmit} className="tool-form">

            <div className="form-group">
              <label className="field-label">Желаемая специализация</label>
              <div className="field-chips">
                {careerFields.map(f => (
                  <button
                    type="button"
                    key={f}
                    className={`skill-chip ${careerField === f ? 'selected' : ''}`}
                    onClick={() => setCareerField(f)}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="field-label">Резюме (PDF или DOCX)</label>
              <label className="file-upload-box">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={e => setResumeFile(e.target.files[0] || null)}
                  disabled={loading}
                />
                <div className="file-box-inner">
                  {resumeFile ? (
                    <>
                      <span className="file-icon">📎</span>
                      <span className="file-name">{resumeFile.name}</span>
                      <span className="file-size">
                        {(resumeFile.size / 1024).toFixed(0)} КБ
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="file-placeholder">
                        Нажмите или перетащите файл сюда
                      </span>
                      <span className="file-hint">PDF, DOCX, TXT</span>
                    </>
                  )}
                </div>
              </label>
            </div>

            {error && <p className="error-msg">{error}</p>}

            <button className="btn-primary submit-btn" type="submit" disabled={loading}>
              {loading
                ? <><span className="spinner" /> Анализируем резюме…</>
                : 'Проанализировать резюме →'
              }
            </button>
          </form>

          <div className="tool-hint">
            <strong>Что анализируем:</strong> опыт работы, образование, технические навыки,
            портфолио на GitHub, соответствие выбранной специализации.
            AI-модель добавит персональный комментарий HR-консультанта.
          </div>
        </div>
      </main>
    </div>
  );
}
