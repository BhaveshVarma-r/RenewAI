import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE, timeout: 300000 });

export const triggerDueDate = (policyId: string, daysToDue: number) =>
    api.post('/trigger/due-date', { policy_id: policyId, days_to_due: daysToDue });

export const triggerInbound = (policyId: string, channel: string, message: string, phone: string) =>
    api.post('/trigger/inbound', { policy_id: policyId, channel, message, phone });

export const triggerLapse = (policyId: string, daysSinceLapse: number) =>
    api.post('/trigger/lapse', { policy_id: policyId, days_since_lapse: daysSinceLapse });

export const triggerBatchScan = (days: number) => api.post(`/trigger/scan/t-minus/${days}`);

export const getAuditTrace = (traceId: string) => api.get(`/audit/trace/${traceId}`);
export const getAuditPolicy = (policyId: string) => api.get(`/audit/policy/${policyId}`);
export const getPendingQueue = () => api.get('/queue/pending');
export const resolveQueueCase = (queueId: string, resolution: string, notes: string) =>
    api.post(`/queue/resolve/${queueId}`, { resolution, specialist_notes: notes });
export const getKPISummary = () => api.get('/kpi/summary');
export const getHealth = () => api.get('/health');
export const runDemo = () => api.post('/demo/run-all');
export const getPolicies = () => api.get('/policies');
export const getPolicy = (policyId: string) => api.get(`/policies/${policyId}`);

export default api;
