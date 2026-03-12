import { useState, useCallback } from 'react';
import { auditAPI } from '../services/api';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import Header from '../components/shared/Header';
import StatusBadge from '../components/shared/StatusBadge';
import {
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';

function CritiqueCard({ critique }) {
  const [expanded, setExpanded] = useState(false);

  let issues = [];
  let scores = {};
  try {
    issues =
      typeof critique.specific_issues === 'string'
        ? JSON.parse(critique.specific_issues)
        : critique.specific_issues || [];
    scores =
      typeof critique.dimension_scores === 'string'
        ? JSON.parse(critique.dimension_scores)
        : critique.dimension_scores || {};
  } catch (e) {}

  const borderColor =
    critique.verdict === 'APPROVED'
      ? 'border-emerald-200'
      : critique.verdict === 'REJECTED'
      ? 'border-red-200'
      : 'border-amber-200';

  return (
    <div className={'bg-white rounded-xl border shadow-sm overflow-hidden ' + borderColor}>
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-800 text-sm">
                {critique.critique_agent?.toUpperCase()}
              </span>
              <span className="text-gray-400 text-sm">reviewed</span>
              <span className="text-gray-600 text-sm font-medium">
                {critique.target_agent}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              {new Date(critique.timestamp).toLocaleString()}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-gray-400">Score</p>
              <p className="text-lg font-bold text-gray-700">
                {((critique.overall_score || 0) * 100).toFixed(0)}%
              </p>
            </div>
            <StatusBadge status={critique.verdict} />
            {expanded ? (
              <ChevronDown size={16} className="text-gray-400" />
            ) : (
              <ChevronRight size={16} className="text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-100 pt-4">
          {Object.keys(scores).length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Dimension Scores
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {Object.entries(scores).map(([dim, score]) => (
                  <div key={dim} className="bg-gray-50 rounded-lg p-2.5">
                    <p className="text-xs text-gray-500 capitalize">
                      {dim.replace(/_/g, ' ')}
                    </p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                        <div
                          className={
                            'h-1.5 rounded-full transition-all ' +
                            (score >= 0.8
                              ? 'bg-emerald-500'
                              : score >= 0.6
                              ? 'bg-amber-500'
                              : 'bg-red-500')
                          }
                          style={{ width: score * 100 + '%' }}
                        />
                      </div>
                      <span className="text-xs font-medium text-gray-700">
                        {(score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {issues.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Issues Found ({issues.length})
              </p>
              <div className="space-y-2">
                {issues.map((issue, i) => (
                  <div
                    key={i}
                    className={
                      'rounded-lg p-3 text-sm ' +
                      (issue.severity === 'BLOCKING'
                        ? 'bg-red-50 text-red-800'
                        : issue.severity === 'SIGNIFICANT'
                        ? 'bg-amber-50 text-amber-800'
                        : 'bg-gray-50 text-gray-700')
                    }
                  >
                    <div className="flex items-center gap-1.5 font-medium mb-1">
                      <AlertTriangle size={12} />
                      [{issue.severity}]{' '}
                      {issue.dimension && (
                        <span className="opacity-70">{issue.dimension}</span>
                      )}
                    </div>
                    <p className="text-xs leading-relaxed">{issue.issue}</p>
                    {issue.correction && (
                      <p className="text-xs mt-1.5 opacity-75 border-t border-current border-opacity-20 pt-1.5">
                        Fix: {issue.correction}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {critique.critique_reasoning && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                Critique Reasoning
              </p>
              <p className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 leading-relaxed">
                {critique.critique_reasoning?.slice(0, 600)}
                {critique.critique_reasoning?.length > 600 ? '...' : ''}
              </p>
            </div>
          )}

          {critique.escalated_to_human === 1 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 flex items-center gap-2">
              <AlertTriangle size={13} className="text-orange-600" />
              <span className="text-xs text-orange-700 font-medium">
                Escalated to human review
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AuditPage() {
  const [tab, setTab] = useState('critiques');
  const [reviewer, setReviewer] = useState('Head of Operations');

  const fetchCritiques = useCallback(
    () => auditAPI.getCritiques(50),
    []
  );
  const fetchAuditLog = useCallback(
    () => auditAPI.getLog(100),
    []
  );
  const fetchApprovals = useCallback(
    () => auditAPI.getApprovals(),
    []
  );

  const { data: critiquesData, refresh: refreshCritiques } = useAutoRefresh(
    fetchCritiques,
    30000,
    []
  );
  const { data: auditData, refresh: refreshAudit } = useAutoRefresh(
    fetchAuditLog,
    30000,
    []
  );
  const { data: approvalsData, refresh: refreshApprovals } = useAutoRefresh(
    fetchApprovals,
    15000,
    []
  );

  const critiques = critiquesData?.critiques || [];
  const auditLog = auditData?.logs || [];
  const approvals = approvalsData?.approvals || [];
  const pendingApprovals = approvals.filter((a) => a.status === 'pending');

  const handleApproval = async (approvalId, action) => {
    await auditAPI.processApproval({
      approval_id: approvalId,
      action,
      reviewer,
    });
    refreshApprovals();
  };

  const tabs = [
    { id: 'critiques', label: 'Critique Log', count: critiques.length },
    { id: 'approvals', label: 'Approvals Queue', count: pendingApprovals.length, urgent: pendingApprovals.length > 0 },
    { id: 'audit', label: 'Audit Log', count: auditLog.length },
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header title="Audit and Critique" />
      <div className="flex-1 overflow-auto p-6 bg-gray-50">

        <div className="flex gap-1 bg-white rounded-xl p-1 border border-gray-200 shadow-sm mb-6 w-fit">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={
                'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ' +
                (tab === t.id
                  ? 'bg-emerald-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100')
              }
            >
              {t.label}
              {t.count > 0 && (
                <span
                  className={
                    'text-xs px-1.5 py-0.5 rounded-full ' +
                    (tab === t.id
                      ? 'bg-emerald-500 text-white'
                      : t.urgent
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-200 text-gray-600')
                  }
                >
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {tab === 'critiques' && (
          <div className="space-y-3">
            {critiques.length === 0 ? (
              <div className="bg-white rounded-xl p-10 text-center text-gray-400 border border-gray-200">
                <FileText size={32} className="mx-auto mb-3 opacity-30" />
                <p>No critique records yet</p>
                <p className="text-xs mt-1">
                  Run an agent pipeline to see critiques here
                </p>
              </div>
            ) : (
              critiques.map((c, i) => <CritiqueCard key={i} critique={c} />)
            )}
          </div>
        )}

        {tab === 'approvals' && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
              <label className="text-sm text-gray-600 font-medium shrink-0">
                Reviewer:
              </label>
              <input
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm flex-1 max-w-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {pendingApprovals.length === 0 ? (
              <div className="bg-white rounded-xl p-10 text-center text-gray-400 border border-gray-200">
                <CheckCircle size={32} className="mx-auto mb-3 text-emerald-400" />
                <p>No pending approvals</p>
              </div>
            ) : (
              pendingApprovals.map((a) => (
                <div
                  key={a.approval_id}
                  className="bg-white rounded-xl p-5 border border-amber-200 shadow-sm"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <p className="font-semibold text-gray-800">
                        {a.action_description}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {a.agent_name} · Authority required:{' '}
                        {a.authority_required} ·{' '}
                        {new Date(a.created_at).toLocaleString()}
                      </p>
                    </div>
                    <StatusBadge status={a.urgency || 'HIGH'} />
                  </div>
                  <div className="flex gap-3 mt-4">
                    <button
                      onClick={() =>
                        handleApproval(a.approval_id, 'approved')
                      }
                      className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-all shadow-sm"
                    >
                      <CheckCircle size={14} />
                      Approve
                    </button>
                    <button
                      onClick={() =>
                        handleApproval(a.approval_id, 'rejected')
                      }
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-all shadow-sm"
                    >
                      <XCircle size={14} />
                      Reject
                    </button>
                  </div>
                </div>
              ))
            )}

            {approvals.filter((a) => a.status !== 'pending').length > 0 && (
              <div>
                <p className="text-sm font-semibold text-gray-600 mb-3">
                  Processed Approvals
                </p>
                {approvals
                  .filter((a) => a.status !== 'pending')
                  .slice(0, 10)
                  .map((a) => (
                    <div
                      key={a.approval_id}
                      className="bg-white rounded-xl p-4 border border-gray-200 mb-2 opacity-70"
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-gray-600">
                          {a.action_description}
                        </p>
                        <StatusBadge status={a.status} />
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        By {a.reviewed_by || 'unknown'} at{' '}
                        {a.reviewed_at
                          ? new Date(a.reviewed_at).toLocaleString()
                          : '—'}
                      </p>
                    </div>
                  ))}
              </div>
            )}
          </div>
        )}

        {tab === 'audit' && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-800">
                System Audit Log
              </h3>
              <p className="text-xs text-gray-400">
                Auto-refreshes every 30s
              </p>
            </div>
            <div className="divide-y divide-gray-50 max-h-screen overflow-y-auto">
              {auditLog.length === 0 ? (
                <div className="p-8 text-center text-gray-400">
                  No audit records yet
                </div>
              ) : (
                auditLog.map((item, i) => (
                  <div
                    key={i}
                    className="px-5 py-3 flex items-start gap-3 hover:bg-gray-50"
                  >
                    <Clock
                      size={13}
                      className="text-gray-400 mt-0.5 shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 leading-snug">
                        {item.action_description}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {new Date(item.timestamp).toLocaleString()} ·{' '}
                        {item.agent_name || 'system'}
                      </p>
                    </div>
                    <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded shrink-0 font-mono">
                      {item.event_type?.slice(0, 25)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}