import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar     from '../components/Sidebar';
import ClusterCard from '../components/ClusterCard';
import './ClusterSelectPage.css';

export default function ClusterSelectPage() {
  const navigate = useNavigate();
  const [surveyData, setSurveyData]     = useState(null);
  const [selectedClusters, setSelected] = useState(new Set());
  const [error, setError]               = useState('');

  useEffect(() => {
    const raw = sessionStorage.getItem('surveyResult');
    if (!raw) { navigate('/'); return; }
    const data = JSON.parse(raw);
    setSurveyData(data);
    setSelected(new Set([data.clusterId]));
  }, [navigate]);

  function toggleCluster(cid) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(cid) ? next.delete(cid) : next.add(cid);
      return next;
    });
  }

  function handleSubmit() {
    if (selectedClusters.size === 0) {
      setError('Пожалуйста, выберите хотя бы один кластер.');
      return;
    }
    setError('');
    sessionStorage.setItem('clusterSelection', JSON.stringify({
      selectedClusters:     [...selectedClusters],
      clusterIdRecommended: surveyData.clusterId,
      workFormats:          surveyData.workFormats  || [],
      salaryFrom:           surveyData.salaryFrom   || null,
      salaryTo:             surveyData.salaryTo     || null,
      skillFilters:         [],
    }));
    navigate('/result');
  }

  if (!surveyData) return null;

  const { clusterName, clustersList = [] } = surveyData;

  return (
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <div className="card">
            <h1 className="page-title">🗂️ Выбор кластеров для анализа</h1>
            <p className="page-subtitle">
              Выберите один или несколько кластеров — мы покажем вакансии из каждого.
            </p>

            <div className="recommended-badge">
              ⭐ Ваш рекомендованный кластер: <strong>{clusterName}</strong>
            </div>

            <div className="clusters-grid">
              {clustersList.map(cluster => (
                  <ClusterCard
                      key={cluster.cid}
                      cluster={cluster}
                      isSelected={selectedClusters.has(cluster.cid)}
                      isRecommended={cluster.cid === surveyData.clusterId}
                      onToggle={toggleCluster}
                  />
              ))}
            </div>

            <p className="selection-counter">
              Выбрано кластеров: <strong>{selectedClusters.size}</strong>
            </p>

            {error && <p className="error-msg">{error}</p>}

            <button className="btn-primary submit-btn" onClick={handleSubmit}>
              Смотреть вакансии →
            </button>
          </div>
        </main>
      </div>
  );
}