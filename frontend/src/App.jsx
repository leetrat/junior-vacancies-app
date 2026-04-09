import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import SurveyPage         from './pages/SurveyPage';
import ClusterSelectPage  from './pages/ClusterSelectPage';
import ResultPage         from './pages/ResultPage';
import VacancyPage        from './pages/VacancyPage';
import VacancyResultPage  from './pages/VacancyResultPage';
import ResumePage         from './pages/ResumePage';
import ResumeResultPage   from './pages/ResumeResultPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SurveyPage />} />
      <Route path="/clusters"element={<ClusterSelectPage />} />
      <Route path="/result" element={<ResultPage />} />
      <Route path="/vacancy" element={<VacancyPage />} />
      <Route path="/vacancy/result" element={<VacancyResultPage />} />
      <Route path="/resume" element={<ResumePage />} />
      <Route path="/resume/result" element={<ResumeResultPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
