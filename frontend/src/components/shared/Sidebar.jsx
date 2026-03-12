import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Thermometer,
  Activity,
  Users,
  Package,
  FileText,
  Settings,
  Zap,
} from 'lucide-react';

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/cold-chain', icon: Thermometer, label: 'Cold Chain' },
  { to: '/epidemic', icon: Activity, label: 'Epidemic Radar' },
  { to: '/staffing', icon: Users, label: 'Staffing' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/audit', icon: FileText, label: 'Audit & Critique' },
  { to: '/prompts', icon: Settings, label: 'Prompt Registry' },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-900 text-white flex flex-col z-50 shadow-2xl">
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg">
            <Zap size={18} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-lg leading-none tracking-tight">
              PharmaIQ
            </div>
            <div className="text-xs text-slate-400 mt-0.5">MedChain India</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ' +
              (isActive
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white')
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-700">
        <div className="text-xs text-slate-500 text-center leading-relaxed">
          320 Stores
          <br />
          4.2M Patients Annually
        </div>
      </div>
    </aside>
  );
}