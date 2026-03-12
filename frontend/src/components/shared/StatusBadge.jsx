const VARIANTS = {
  CRITICAL: 'bg-red-100 text-red-800 border border-red-200',
  HIGH: 'bg-orange-100 text-orange-800 border border-orange-200',
  MODERATE: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
  MEDIUM: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
  LOW: 'bg-blue-100 text-blue-800 border border-blue-200',
  NORMAL: 'bg-emerald-100 text-emerald-800 border border-emerald-200',
  BREACH: 'bg-red-100 text-red-800 border border-red-200',
  APPROVED: 'bg-emerald-100 text-emerald-800 border border-emerald-200',
  REJECTED: 'bg-red-100 text-red-800 border border-red-200',
  APPROVED_WITH_MODIFICATIONS:
    'bg-amber-100 text-amber-800 border border-amber-200',
  ALERT: 'bg-orange-100 text-orange-800 border border-orange-200',
  OUTBREAK: 'bg-red-100 text-red-800 border border-red-200',
  WATCH: 'bg-blue-100 text-blue-800 border border-blue-200',
  EPIDEMIC: 'bg-purple-100 text-purple-800 border border-purple-200',
  pending: 'bg-gray-100 text-gray-700 border border-gray-200',
  confirmed: 'bg-emerald-100 text-emerald-800 border border-emerald-200',
  delivered: 'bg-blue-100 text-blue-800 border border-blue-200',
  COMPLETE: 'bg-emerald-100 text-emerald-800 border border-emerald-200',
  HUMAN_REQUIRED: 'bg-red-100 text-red-800 border border-red-200',
  PARTIAL: 'bg-amber-100 text-amber-800 border border-amber-200',
};

export default function StatusBadge({ status, size = 'sm' }) {
  const classes = VARIANTS[status] || 'bg-gray-100 text-gray-600 border border-gray-200';
  const sizeClass =
    size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';
  return (
    <span
      className={
        'inline-flex items-center rounded-full font-medium ' +
        classes +
        ' ' +
        sizeClass
      }
    >
      {status}
    </span>
  );
}