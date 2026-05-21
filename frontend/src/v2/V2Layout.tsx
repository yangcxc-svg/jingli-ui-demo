/**
 * v2 外壳布局：仿 iOS 手机壳 + 状态栏 + 灵动岛 + Toast + 底部 tab。
 * 子页面通过 <Outlet /> 渲染到滚动主区。
 */
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { Icon, type IconName } from './components/Icon';
import { V2Provider, useV2 } from './state/V2Context';

const TIME_LABEL = '15:26';

interface TabDef {
  to: string;
  label: string;
  icon: IconName;
  matchPaths?: string[];
}

const TABS: TabDef[] = [
  { to: '/v2/home', label: '首 页', icon: 'home', matchPaths: ['/v2', '/v2/home'] },
  {
    to: '/v2/wizard',
    label: 'AI送礼',
    icon: 'sparkles',
    matchPaths: ['/v2/wizard', '/v2/recommendations'],
  },
  { to: '/v2/cart', label: '购物车', icon: 'shopping-bag' },
  { to: '/v2/orders', label: '物流单', icon: 'truck' },
];

function StatusBar() {
  const { island } = useV2();
  return (
    <div className="relative z-50 flex h-11 select-none items-center justify-between bg-[#f8f9fb] px-6">
      <span className="text-[12px] font-bold text-slate-900">{TIME_LABEL}</span>
      <div
        className={`absolute left-1/2 top-2 z-50 flex -translate-x-1/2 items-center rounded-3xl transition-all duration-500 ease-out ${
          island
            ? 'w-[320px] border border-rose-100 bg-white px-4 py-2 shadow-lg'
            : 'h-[26px] w-[110px] bg-black shadow-md'
        }`}
      >
        {island ? (
          <div className="flex w-full items-center space-x-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-full border border-rose-100 bg-rose-50 animate-pulse">
              <Icon name="sparkles" className="h-3.5 w-3.5 text-[#e4393c]" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-[11px] font-bold leading-tight text-slate-950">{island.title}</p>
              <p className="mt-0.5 truncate text-[9px] leading-tight text-slate-500">
                {island.subtitle}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex w-full items-center justify-center space-x-1">
            <div className="h-2 w-2 rounded-full bg-slate-800" />
            <div className="h-[10px] w-[10px] rounded-full border border-slate-900 bg-[#111]" />
          </div>
        )}
      </div>
      <div className="flex items-center space-x-1.5 text-slate-900">
        <span className="text-[10px]">5G</span>
        <div className="flex h-2.5 w-5 items-center rounded-sm border border-slate-900 p-[1px]">
          <div className="h-full w-4 rounded-[1px] bg-slate-900" />
        </div>
      </div>
    </div>
  );
}

function ToastSlot() {
  const { toast } = useV2();
  if (!toast) return null;
  return (
    <div className="absolute left-4 right-4 top-16 z-50 flex items-center space-x-2 rounded-xl border border-red-100 bg-white px-4 py-2.5 text-[11px] text-red-500 shadow-lg animate-bounce">
      <Icon name="info" className="h-4 w-4 shrink-0 text-red-400" />
      <span className="truncate">{toast}</span>
    </div>
  );
}

function LoadingMask() {
  const { loading } = useV2();
  if (!loading) return null;
  return (
    <div className="absolute inset-0 z-50 flex flex-col items-center justify-center space-y-4 bg-black/90">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-indigo-600/20 border-t-indigo-500" />
      <p className="animate-pulse text-[13px] font-semibold tracking-wider text-indigo-400">
        AI 深度推理转译中...
      </p>
    </div>
  );
}

function BottomTabs() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  return (
    <div className="absolute bottom-0 left-0 right-0 z-40 flex h-16 items-center justify-around border-t border-slate-200/80 bg-white/96 px-4 pb-2 shadow-[0_-10px_24px_rgba(15,23,42,0.06)] backdrop-blur">
      {TABS.map((tab) => {
        const matched = (tab.matchPaths ?? [tab.to]).some((p) => pathname === p || pathname.startsWith(p + '/'));
        return (
          <button
            key={tab.to}
            onClick={() => navigate(tab.to)}
            className={`flex flex-col items-center space-y-1 transition-colors ${
              matched ? 'text-[#e4393c]' : 'text-slate-400'
            }`}
          >
            <Icon name={tab.icon} className="h-[17px] w-[17px]" />
            <span className="text-[9px] font-bold">{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function V2Shell() {
  return (
    <div className="relative flex h-full w-full flex-col bg-[#f8f9fb] text-slate-950">
      <StatusBar />
      <LoadingMask />
      <ToastSlot />
      <div className="no-scrollbar flex-1 overflow-y-auto pb-20">
        <Outlet />
      </div>
      <BottomTabs />
    </div>
  );
}

export default function V2Layout() {
  return (
    <V2Provider>
      <V2Shell />
    </V2Provider>
  );
}
