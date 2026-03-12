import { useState, useCallback } from 'react';
import { promptsAPI } from '../services/api';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import Header from '../components/shared/Header';
import { Settings, CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react';

export default function PromptsPage() {
  const [switchingAgent, setSwitchingAgent] = useState(null);
  const [switchMessage, setSwitchMessage] = useState('');
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  const fetchRegistry = useCallback(() => promptsAPI.getRegistry(), []);

  const { data: registryData, refresh } = useAutoRefresh(fetchRegistry, 0, []);

  const registry = registryData || {};
  const activeVersions = registry.active_versions || {};
  const agents = registry.agents || [];
  const metadata = registry.metadata || {};

  const handleVersionSwitch = async (agent, version) => {
    setSwitchingAgent(agent);
    setSwitchMessage('');
    try {
      await promptsAPI.updateVersion(agent, version);
      setSwitchMessage('Version updated to ' + version + ' for ' + agent);
      refresh();
    } catch (e) {
      setSwitchMessage(
        'Error: ' + (e.response?.data?.detail || e.message)
      );
    } finally {
      setSwitchingAgent(null);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    try {
      const r = await promptsAPI.validate();
      setValidationResult(r.data);
    } catch (e) {
      setValidationResult({ status: 'error', error: e.message });
    } finally {
      setValidating(false);
    }
  };

  const agentColors = {
    soma: 'bg-blue-50 border-blue-200',
    soma_critique: 'bg-blue-50 border-blue-200',
    pulse: 'bg-emerald-50 border-emerald-200',
    pulse_critique: 'bg-emerald-50 border-emerald-200',
    planner: 'bg-purple-50 border-purple-200',
    planner_critique: 'bg-purple-50 border-purple-200',
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header title="Prompt Registry" />
      <div className="flex-1 overflow-auto p-6 bg-gray-50">

        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              Agent Prompt Version Control
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Manage prompt versions for all agents. Changes take effect
              immediately.
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleValidate}
              disabled={validating}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              <CheckCircle size={14} />
              {validating ? 'Validating...' : 'Validate All'}
            </button>
            <button
              onClick={refresh}
              className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-500 hover:bg-gray-50"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        {switchMessage && (
          <div
            className={
              'mb-4 px-4 py-3 rounded-lg text-sm font-medium border ' +
              (switchMessage.startsWith('Error')
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-emerald-50 border-emerald-200 text-emerald-700')
            }
          >
            {switchMessage}
          </div>
        )}

        {validationResult && (
          <div
            className={
              'mb-6 bg-white rounded-xl border shadow-sm p-4 ' +
              (validationResult.status === 'ok'
                ? 'border-emerald-200'
                : 'border-red-200')
            }
          >
            <div className="flex items-center gap-2 mb-3">
              {validationResult.status === 'ok' ? (
                <CheckCircle size={16} className="text-emerald-600" />
              ) : (
                <AlertTriangle size={16} className="text-red-600" />
              )}
              <p className="font-semibold text-gray-800 text-sm">
                Validation{' '}
                {validationResult.status === 'ok' ? 'Passed' : 'Found Issues'}
              </p>
            </div>
            {validationResult.errors?.length > 0 && (
              <div className="space-y-1">
                {validationResult.errors.map((e, i) => (
                  <p key={i} className="text-xs text-red-600 font-mono">
                    {e}
                  </p>
                ))}
              </div>
            )}
            {validationResult.status === 'ok' && (
              <p className="text-xs text-emerald-600">
                All prompt files loaded successfully
              </p>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {agents.map((agent) => {
            const meta = metadata[agent] || {};
            const activeVersion = activeVersions[agent];
            const agentVersions = meta.versions_available || [];
            const promptFiles = Object.keys(meta.prompts || {});

            return (
              <div
                key={agent}
                className={
                  'bg-white rounded-xl border shadow-sm overflow-hidden ' +
                  (agentColors[agent] || 'border-gray-200')
                }
              >
                <div
                  className={
                    'px-5 py-4 border-b ' +
                    (agentColors[agent]?.replace('bg-', 'bg-').replace('border-', 'border-') ||
                      'border-gray-100 bg-gray-50')
                  }
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-gray-800 uppercase tracking-wide text-sm">
                        {agent}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {meta.description || 'No description'}
                      </p>
                    </div>
                    <div className="bg-white border border-gray-200 px-3 py-1 rounded-full text-sm font-bold text-gray-700">
                      {activeVersion}
                    </div>
                  </div>
                </div>

                <div className="p-4 space-y-3">
                  {meta.changelog && (
                    <div className="bg-gray-50 rounded-lg px-3 py-2">
                      <p className="text-xs text-gray-500 font-medium mb-0.5">
                        Changelog
                      </p>
                      <p className="text-xs text-gray-600">{meta.changelog}</p>
                    </div>
                  )}

                  {promptFiles.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                        Prompt Files
                      </p>
                      <div className="flex gap-1.5 flex-wrap">
                        {promptFiles.map((f) => (
                          <span
                            key={f}
                            className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono"
                          >
                            {f}.txt
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <VersionSwitcher
                    agent={agent}
                    activeVersion={activeVersion}
                    onSwitch={handleVersionSwitch}
                    switching={switchingAgent === agent}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function VersionSwitcher({ agent, activeVersion, onSwitch, switching }) {
  const [versions, setVersions] = useState(null);
  const [expanded, setExpanded] = useState(false);

  const loadVersions = async () => {
    if (!expanded && !versions) {
      const r = await promptsAPI.getAgentVersions(agent);
      setVersions(r.data.versions || []);
    }
    setExpanded(!expanded);
  };

  return (
    <div>
      <button
        onClick={loadVersions}
        className="text-xs text-emerald-600 hover:text-emerald-700 font-medium underline"
      >
        {expanded ? 'Hide versions' : 'Switch version'}
      </button>

      {expanded && versions && (
        <div className="mt-2 flex gap-2 flex-wrap">
          {versions.map((v) => (
            <button
              key={v}
              onClick={() => onSwitch(agent, v)}
              disabled={switching || v === activeVersion}
              className={
                'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' +
                (v === activeVersion
                  ? 'bg-emerald-600 text-white border-emerald-600 cursor-default'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-emerald-400 hover:text-emerald-600 disabled:opacity-50')
              }
            >
              {switching && v !== activeVersion ? 'Switching...' : v}
              {v === activeVersion && ' (active)'}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}