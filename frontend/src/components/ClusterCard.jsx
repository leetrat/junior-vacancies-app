import React from 'react';
import './ClusterCard.css';

/**
 *   cluster:     { cid, name, descriptionShort, techTagClass,
 *                  techLabel, overworkTagClass, overworkLabel }
 *   isSelected:  bool
 *   isRecommended: bool
 *   onToggle:    (cid) => void
 */
export default function ClusterCard({ cluster, isSelected, isRecommended, onToggle }) {
  const { cid, name, descriptionShort, techTagClass, techLabel, overworkTagClass, overworkLabel } = cluster;

  return (
      <div
          className={`cluster-card ${isSelected ? 'selected' : ''} ${isRecommended ? 'recommended' : ''}`}
          onClick={() => onToggle(cid)}
      >
          <input type="checkbox" checked={isSelected} readOnly/>
          <div className="cc-body">
            <div className="cc-name">{name}</div>
            <div className="cc-desc">{descriptionShort}</div>
            <div className="cc-tags">
              <span className={`tag ${techTagClass}`}>{techLabel}</span>
              <span className={`tag ${overworkTagClass}`}>{overworkLabel}</span>
            </div>
          </div>
      </div>
);
}
