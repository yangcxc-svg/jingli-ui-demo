import { useEffect, useState, type ReactNode } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom';

const topTabs = ['特价', '首页', '秒送', '外卖', '新品'];
const channels = ['关注', '推荐', '国家补贴', '手机', '电脑办公', '爱车', '分类'];
const shortcuts = [
  { label: '秒杀', icon: '⚡', badge: '领京豆', tone: 'from-red-500 to-orange-400' },
  { label: '火车票', icon: '🚄', tone: 'from-sky-500 to-blue-400' },
  { label: '机票', icon: '🎫', tone: 'from-indigo-500 to-violet-400' },
  { label: '京东家政', icon: '🏠', tone: 'from-rose-500 to-red-400' },
  { label: '领券中心', icon: '券', badge: '千万券', tone: 'from-orange-500 to-red-400' },
  { label: 'PLUS', icon: '♛', tone: 'from-amber-400 to-yellow-300' },
];
const lifeEntries = [
  { label: '宿迁', icon: '🏙️' },
  { label: '超市秒送', icon: '🛒' },
  { label: '买药秒送', icon: '💊' },
  { label: '外卖', icon: '🍱' },
  { label: '美食团购', icon: '🍜' },
  { label: '京东旅行', icon: '🧳' },
];
const promoItems = [
  { label: '厨电购物季', icon: '🍳' },
  { label: '运动健身', icon: '🏃' },
  { label: '水饮冲调', icon: '🥤' },
  { label: '抽百万免单 健康精选好物', icon: '🎁' },
];
const bottomTabs = ['首页', '极米', '消息', '购物车', '我的'];
const giftScenes = [
  { title: '生日礼物', icon: '🎂', desc: '朋友、同事、家人生日', active: true },
  { title: '见家长', icon: '🏠', desc: '体面不出错' },
  { title: '情侣纪念日', icon: '💝', desc: '浪漫、有心意' },
  { title: '送领导/客户', icon: '🤝', desc: '稳重、有分寸' },
  { title: '乔迁新居', icon: '🏡', desc: '实用、有品质' },
  { title: '探望长辈', icon: '🍵', desc: '健康、实用' },
  { title: '婚礼/订婚', icon: '💍', desc: '喜庆、有档次' },
  { title: '节日送礼', icon: '🎁', desc: '春节、中秋、端午' },
];
const giftProducts = [
  {
    name: '香氛礼盒',
    price: '¥399',
    tags: ['氛围感', '女生礼物'],
    reason: '颜值高，适合生日和纪念日场景',
    icon: '🎁',
    tone: 'from-pink-100 to-violet-100',
  },
  {
    name: '数码小配件',
    price: '¥299',
    tags: ['精致', '高性价比'],
    reason: '预算友好，适合年轻用户日常使用，礼物感轻松不冒犯',
    icon: '🎧',
    tone: 'from-sky-100 to-indigo-100',
  },
  {
    name: '精致护肤套装',
    price: '¥499',
    tags: ['体面', '热卖'],
    reason: '预算内更显品质，适合关系较亲近的人',
    icon: '🧴',
    tone: 'from-rose-100 to-orange-100',
  },
];
const quickQuestions = ['送女朋友生日礼物', '见家长带什么合适', '送领导不尴尬', '给爸妈买健康礼物'];
const comboProducts = [
  {
    name: '高端茶礼礼盒',
    price: '¥699',
    icon: '🍵',
    tags: ['体面', '长辈友好'],
    reason: '适合正式拜访场景，稳重、不冒犯，是传统长辈礼品中的安全选择。',
    tone: 'from-emerald-50 to-lime-100',
  },
  {
    name: '智能按摩仪',
    price: '¥899',
    icon: '💆',
    tags: ['健康', '实用'],
    reason: '体现对长辈健康的关心，实用价值高，比单纯礼盒更有心意。',
    tone: 'from-sky-50 to-violet-100',
  },
  {
    name: '滋补养生礼盒',
    price: '¥799',
    icon: '🎁',
    tags: ['养生', '有分量'],
    reason: '强化送礼分量感，适合长辈场景，也更符合正式拜访预期。',
    tone: 'from-red-50 to-orange-100',
  },
  {
    name: '品质坚果礼盒',
    price: '¥589',
    icon: '🥜',
    tags: ['全家共享', '补充搭配'],
    reason: '适合家庭一起分享，让礼物更自然，也避免全部礼物都过于正式。',
    tone: 'from-amber-50 to-yellow-100',
  },
];
const valuePoints = [
  { title: '体面感', icon: '🎩', desc: '茶礼和滋补礼盒承担正式送礼属性，不显随意。', tone: 'bg-red-50 text-red-600' },
  { title: '实用性', icon: '💆', desc: '按摩仪体现对健康的关心，避免礼物只停留在表面。', tone: 'bg-violet-50 text-violet-600' },
  { title: '家庭共享', icon: '🥜', desc: '坚果礼盒适合全家一起享用，让礼物更自然。', tone: 'bg-amber-50 text-amber-700' },
];
const comboChips = ['更高端', '更健康', '更稳妥', '控制在 2500 内', '增加科技感'];
const premiumProducts = [
  {
    name: '高端茗茶礼盒',
    price: '¥1299',
    icon: '🍵',
    tags: ['体面', '高端礼盒'],
    reason: '作为主礼之一，适合正式拜访场景，稳重且不容易出错。',
    tone: 'from-emerald-50 to-lime-100',
  },
  {
    name: '智能肩颈按摩仪 Pro',
    price: '¥1399',
    icon: '💆',
    tags: ['健康', '品质升级'],
    reason: '比普通按摩仪更有品质感，能体现对长辈健康的关心。',
    tone: 'from-sky-50 to-violet-100',
  },
  {
    name: '高端滋补礼盒',
    price: '¥1299',
    icon: '🎁',
    tags: ['养生', '有分量'],
    reason: '增强礼单的正式感和分量感，适合长辈送礼场景。',
    tone: 'from-red-50 to-orange-100',
  },
  {
    name: '进口坚果礼盒',
    price: '¥971',
    icon: '🥜',
    tags: ['全家共享', '补充搭配'],
    reason: '适合家庭一起分享，让整套礼物更自然，不显得过于功利。',
    tone: 'from-amber-50 to-yellow-100',
  },
];
const premiumValuePoints = [
  { title: '主礼更体面', icon: '🎩', desc: '茶礼和滋补礼盒提升正式感，适合长辈场景。', tone: 'bg-red-50 text-red-600' },
  { title: '健康关怀升级', icon: '💆', desc: '按摩仪 Pro 体现更高预算下的实用价值。', tone: 'bg-violet-50 text-violet-600' },
  { title: '兼顾全家感受', icon: '🥜', desc: '坚果礼盒适合家庭分享，降低送礼压迫感。', tone: 'bg-amber-50 text-amber-700' },
];
const premiumChips = ['控制在 4000 内', '更健康', '更商务', '增加酒水', '更适合第一次见面'];
const cartProducts = [
  { name: '高端茶礼礼盒', spec: '礼盒装｜长辈送礼｜体面稳妥', price: '¥699', icon: '🍵', tags: ['京礼推荐', '体面不出错'], tone: 'from-emerald-50 to-lime-100' },
  { name: '智能按摩仪', spec: '肩颈放松｜健康关怀', price: '¥899', icon: '💆', tags: ['健康实用', '长辈适合'], tone: 'from-sky-50 to-violet-100' },
  { name: '滋补养生礼盒', spec: '长辈养生｜正式送礼', price: '¥799', icon: '🎁', tags: ['有分量', '养生礼盒'], tone: 'from-red-50 to-orange-100' },
  { name: '品质坚果礼盒', spec: '全家共享｜补充搭配', price: '¥589', icon: '🥜', tags: ['家庭共享', '自然不尴尬'], tone: 'from-amber-50 to-yellow-100' },
];

function StatusBar() {
  return (
    <div className="flex h-8 items-center justify-between px-5 text-[13px] font-semibold text-zinc-950">
      <span>22:08</span>
      <div className="flex items-center gap-1.5">
        <div className="flex h-3.5 items-end gap-0.5">
          <span className="block h-1.5 w-1 rounded-sm bg-zinc-900" />
          <span className="block h-2 w-1 rounded-sm bg-zinc-900" />
          <span className="block h-2.5 w-1 rounded-sm bg-zinc-900" />
          <span className="block h-3 w-1 rounded-sm bg-zinc-900" />
        </div>
        <span className="text-[11px]">5G</span>
        <div className="flex h-3.5 w-6 items-center rounded-[4px] border border-zinc-900 p-0.5">
          <span className="h-full w-4 rounded-[2px] bg-zinc-900" />
        </div>
      </div>
    </div>
  );
}

function TopNav() {
  const navigate = useNavigate();

  return (
    <div className="grid grid-cols-[auto_1fr_auto] items-center gap-2 px-3 pt-1">
      <div className="flex h-8 items-center gap-1.5 rounded-full bg-white/70 px-1.5 pr-2 shadow-sm ring-1 ring-red-100">
        <span className="grid h-6 w-6 place-items-center rounded-lg bg-gradient-to-br from-red-600 to-red-500 text-[11px] font-black text-white shadow-sm">
          JD
        </span>
        <span className="text-[13px] font-black text-red-600">京东</span>
      </div>
      <div className="flex min-w-0 items-end justify-around gap-1">
        {topTabs.map((tab) => (
          <button
            key={tab}
            className={`relative min-w-0 px-0.5 pb-2 text-[14px] font-semibold ${
              tab === '首页' ? 'text-red-600' : 'text-zinc-700'
            }`}
          >
            {tab}
            {tab === '首页' && (
              <span className="absolute bottom-0 left-1/2 h-1 w-5 -translate-x-1/2 rounded-full bg-red-500" />
            )}
          </button>
        ))}
      </div>
      <button
        onClick={() => {
          console.log('京礼 AI clicked');
          navigate('/jingli');
        }}
        className="flex h-8 items-center gap-1 rounded-full border border-white/80 bg-gradient-to-r from-sky-100 via-violet-100 to-pink-100 px-2.5 text-xs font-black text-violet-700 shadow-[0_8px_20px_rgba(124,58,237,0.18)] ring-1 ring-violet-200/70 transition active:scale-95 active:opacity-80"
      >
        <span className="text-[13px] leading-none">✨</span>
        <span>京礼</span>
      </button>
    </div>
  );
}

function SearchBar() {
  return (
    <div className="mx-3 mt-2 flex h-10 items-center rounded-full border border-red-400 bg-white p-0.5 shadow-soft">
      <div className="flex flex-1 items-center gap-1.5 px-3 text-[13px] text-zinc-800">
        <span className="text-[15px] text-red-500">⌗</span>
        <span className="font-semibold">苹果17pro</span>
        <span className="text-zinc-400">|</span>
        <span className="rounded-full bg-red-50 px-1.5 py-0.5 text-[11px] font-bold text-red-500">超长续航</span>
        <span className="ml-auto rounded-full bg-red-50 px-2 py-0.5 text-xs font-bold text-red-500">AI</span>
      </div>
      <button className="h-8 rounded-full bg-[#e93b3d] px-4 text-sm font-bold text-white shadow-[0_4px_10px_rgba(233,59,61,0.22)]">搜索</button>
    </div>
  );
}

function ChannelBar() {
  return (
    <div className="no-scrollbar mx-3 mt-2 flex gap-3 overflow-x-auto whitespace-nowrap text-[12px] font-bold text-zinc-600">
      {channels.map((item) => (
        <span
          key={item}
          className={`${item === '推荐' ? 'text-red-500' : ''} ${item === '国家补贴' ? 'text-emerald-600' : ''}`}
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function ShortcutGrid() {
  return (
    <div className="mx-3 mt-2 grid grid-cols-6 rounded-2xl bg-white px-1.5 py-2.5 shadow-sm">
      {shortcuts.map((item) => (
        <div key={item.label} className="relative flex flex-col items-center gap-1">
          {item.badge && (
            <span className="absolute -top-1 right-0 rounded-full bg-[#e93b3d] px-1.5 py-0.5 text-[8px] font-black leading-none text-white">
              {item.badge}
            </span>
          )}
          <div className={`grid h-9 w-9 place-items-center rounded-[14px] bg-gradient-to-br ${item.tone} text-[15px] font-black text-white shadow-sm`}>
            {item.icon}
          </div>
          <span className="max-w-[50px] truncate text-[10px] font-bold text-zinc-700">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

function ProductVisual({ type }: { type: 'phone' | 'watch' | 'camera' | 'milk' | 'projector' | 'bottle' }) {
  if (type === 'phone') {
    return (
      <div className="relative h-14 w-9 rounded-[10px] bg-gradient-to-b from-zinc-900 to-zinc-700 p-1 shadow-md">
        <span className="absolute left-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-slate-300" />
        <span className="absolute left-1.5 top-3.5 h-1.5 w-1.5 rounded-full bg-slate-400" />
        <span className="absolute bottom-1 left-1 right-1 h-9 rounded-md bg-gradient-to-br from-blue-500 to-cyan-300" />
      </div>
    );
  }

  if (type === 'watch') {
    return (
      <div className="flex flex-col items-center">
        <span className="h-3 w-5 rounded-t-md bg-zinc-300" />
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-zinc-900 to-zinc-600 shadow-md">
          <span className="h-4 w-4 rounded-full bg-red-400" />
        </span>
        <span className="h-3 w-5 rounded-b-md bg-zinc-300" />
      </div>
    );
  }

  if (type === 'camera') {
    return (
      <div className="relative h-11 w-[52px] rounded-xl bg-gradient-to-br from-zinc-800 to-zinc-500 shadow-md">
        <span className="absolute left-2 top-1.5 h-1.5 w-4 rounded-full bg-zinc-300" />
        <span className="absolute left-1/2 top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-zinc-200 bg-sky-500" />
      </div>
    );
  }

  if (type === 'milk') {
    return (
      <div className="relative h-[52px] w-9 rounded-b-lg rounded-t-sm bg-gradient-to-b from-sky-50 to-blue-200 shadow-md">
        <span className="absolute -top-2 left-1 h-3 w-7 skew-x-[-12deg] rounded-sm bg-white" />
        <span className="absolute bottom-2 left-1 right-1 rounded bg-blue-500 px-0.5 py-0.5 text-[7px] font-black text-white">MILK</span>
      </div>
    );
  }

  if (type === 'projector') {
    return (
      <div className="relative h-11 w-14 rounded-xl bg-gradient-to-br from-slate-800 to-slate-500 shadow-md">
        <span className="absolute right-2 top-2 h-5 w-5 rounded-full border-4 border-slate-200 bg-cyan-500" />
        <span className="absolute bottom-1 left-2 h-1 w-8 rounded-full bg-slate-300" />
      </div>
    );
  }

  return (
    <div className="relative h-14 w-8 rounded-t-xl bg-gradient-to-b from-pink-100 to-rose-300 shadow-md">
      <span className="absolute -top-1 left-2 h-2 w-4 rounded-sm bg-rose-200" />
      <span className="absolute bottom-2 left-1 right-1 rounded bg-white/80 text-center text-[7px] font-black text-rose-600">水</span>
    </div>
  );
}

function MiniProduct({ type, price, tag }: { type: 'phone' | 'watch' | 'camera' | 'milk' | 'projector' | 'bottle'; price: string; tag?: string }) {
  return (
    <div className="relative flex min-w-0 flex-1 flex-col items-center rounded-xl bg-gradient-to-b from-zinc-50 to-white px-1 py-1.5">
      {tag && <span className="absolute left-1 top-1 rounded bg-emerald-500 px-1 text-[8px] font-black text-white">{tag}</span>}
      <div className="grid h-14 place-items-center">
        <ProductVisual type={type} />
      </div>
      <div className="mt-1 text-[12px] font-black leading-none text-[#e93b3d]">{price}</div>
      <div className="mt-0.5 text-[8px] font-bold text-red-500">补贴价</div>
    </div>
  );
}

function FeatureGrid() {
  return (
    <div className="mx-3 mt-2 grid grid-cols-2 gap-2">
      <section className="rounded-2xl bg-white p-2 shadow-sm">
        <h3 className="text-[14px] font-black text-zinc-950">国家补贴 × 百亿补贴</h3>
        <div className="mt-1 flex gap-1.5">
          <MiniProduct type="phone" price="¥79.99" tag="国补" />
          <MiniProduct type="watch" price="¥195" tag="国补" />
        </div>
      </section>

      <section className="rounded-2xl bg-white p-2 shadow-sm">
        <h3 className="text-[14px] font-black text-zinc-950">品质生活</h3>
        <div className="mt-1 grid grid-cols-3 gap-1">
          {lifeEntries.map((entry) => (
            <div key={entry.label} className="flex flex-col items-center rounded-lg bg-red-50/60 px-0.5 py-1">
              <span className="text-[15px] leading-4">{entry.icon}</span>
              <span className="mt-0.5 max-w-[44px] truncate text-[8px] font-bold text-zinc-700">{entry.label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="relative rounded-2xl bg-white p-2 shadow-sm">
        <span className="absolute right-2 top-2 text-[9px] font-black text-red-500">买一送一</span>
        <h3 className="text-[14px] font-black text-zinc-950">9.9包邮</h3>
        <div className="mt-1 flex gap-1.5">
          <MiniProduct type="camera" price="¥7.1" />
          <MiniProduct type="milk" price="¥20.9" />
        </div>
      </section>

      <section className="relative rounded-2xl bg-white p-2 shadow-sm">
        <span className="absolute right-2 top-2 text-[9px] font-black text-red-500">爆品好价</span>
        <h3 className="text-[14px] font-black text-zinc-950">直播</h3>
        <div className="mt-1 flex gap-1.5">
          <MiniProduct type="phone" price="¥7954.1" />
          <MiniProduct type="projector" price="¥690.2" />
        </div>
      </section>
    </div>
  );
}

function PromoBanner() {
  return (
    <div className="mx-3 mt-2 overflow-hidden rounded-2xl bg-gradient-to-r from-[#e93b3d] via-red-500 to-orange-500 p-2.5 text-white shadow-soft">
      <div className="flex items-center justify-between">
        <h2 className="text-[17px] font-black">心动购物季 精选好礼买1送1</h2>
        <button className="rounded-full bg-white px-2.5 py-1 text-[11px] font-black text-[#e93b3d]">立即买</button>
      </div>
      <div className="mt-2 grid grid-cols-4 gap-1.5">
        {promoItems.map((item) => (
          <div key={item.label} className="min-h-[54px] rounded-xl bg-white p-1.5 text-center text-[#e93b3d]">
            <div className="text-lg leading-5">{item.icon}</div>
            <div className="mt-0.5 line-clamp-2 text-[9px] font-black leading-3">{item.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function GiftComboEntryCard() {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate('/combo-chat')}
      className="mx-3 mt-2 block overflow-hidden rounded-2xl bg-gradient-to-r from-violet-50 via-white to-red-50 p-0 text-left shadow-sm ring-1 ring-white transition active:scale-[0.99]"
    >
      <div className="relative flex items-center gap-3 p-3">
        <div className="absolute right-6 top-2 h-16 w-16 rounded-full bg-violet-200/40 blur-2xl" />
        <div className="grid h-12 w-12 flex-none place-items-center rounded-2xl bg-gradient-to-br from-sky-300 via-violet-400 to-pink-300 text-2xl shadow-[0_10px_22px_rgba(124,58,237,0.2)]">
          🎁
        </div>
        <div className="relative min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <h3 className="text-[15px] font-black text-zinc-950">AI 送礼组合方案</h3>
            <span className="rounded-full bg-violet-100 px-1.5 py-0.5 text-[9px] font-black text-violet-700">AI</span>
          </div>
          <p className="mt-1 line-clamp-2 text-[11px] font-bold leading-4 text-zinc-500">
            输入对象、预算和场景，京礼帮你搭配一套体面礼单
          </p>
          <div className="mt-2 flex gap-1.5 overflow-hidden whitespace-nowrap text-[10px] font-black">
            <span className="rounded-full bg-white px-2 py-1 text-[#e93b3d] shadow-sm">老丈人见面礼 ¥3000</span>
            <span className="rounded-full bg-white px-2 py-1 text-violet-600 shadow-sm">生日礼物组合</span>
          </div>
        </div>
        <div className="relative rounded-full bg-[#e93b3d] px-3 py-1.5 text-[11px] font-black text-white shadow-[0_8px_16px_rgba(233,59,61,0.2)]">
          试一试
        </div>
      </div>
    </button>
  );
}

function BottomAdGrid() {
  return (
    <div className="mx-3 mt-2 grid grid-cols-2 gap-2">
      <section className="overflow-hidden rounded-2xl bg-white shadow-sm">
        <div className="grid h-[118px] place-items-center bg-gradient-to-br from-slate-900 to-slate-600">
          <ProductVisual type="phone" />
        </div>
        <div className="p-2">
          <span className="rounded bg-red-50 px-1.5 py-0.5 text-[9px] font-black text-red-500">超长续航</span>
          <h3 className="mt-1 text-[12px] font-black leading-4 text-zinc-900">苹果17 Pro 超长续航</h3>
          <div className="mt-1 text-[17px] font-black text-[#e93b3d]">¥4899</div>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl bg-gradient-to-b from-rose-50 to-white shadow-sm">
        <div className="relative grid h-[118px] place-items-center bg-gradient-to-br from-red-500 to-pink-300">
          <ProductVisual type="bottle" />
          <span className="absolute left-2 top-2 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-black text-red-500">美妆抽奖</span>
        </div>
        <div className="p-2">
          <h3 className="text-[12px] font-black leading-4 text-zinc-900">限定神仙水礼盒</h3>
          <p className="mt-0.5 text-[10px] font-bold text-red-500">红运礼盒 限时加赠</p>
          <button className="mt-1 rounded-full bg-[#e93b3d] px-3 py-1 text-[10px] font-black text-white">立即抽奖</button>
        </div>
      </section>
    </div>
  );
}

function BottomTabBar() {
  return (
    <div className="h-[68px] flex-none border-t border-zinc-200 bg-white px-2 pt-1.5 shadow-[0_-8px_20px_rgba(0,0,0,0.04)]">
      <div className="grid grid-cols-5">
        {bottomTabs.map((tab, index) => (
          <button key={tab} className={`flex flex-col items-center gap-0.5 text-[11px] font-bold ${index === 0 ? 'text-[#e93b3d]' : 'text-zinc-500'}`}>
            <span className={`relative grid h-7 w-7 place-items-center rounded-full ${index === 0 ? 'bg-[#e93b3d] text-white' : 'bg-zinc-100 text-zinc-600'}`}>
              {['⌂', '◇', '✉', '🛒', '☺'][index]}
              {(tab === '消息' || tab === '购物车') && (
                <span className="absolute -right-1 -top-0.5 grid h-3.5 min-w-3.5 place-items-center rounded-full bg-[#e93b3d] px-0.5 text-[8px] font-black leading-none text-white">
                  2
                </span>
              )}
            </span>
            {tab}
          </button>
        ))}
      </div>
    </div>
  );
}

function GiftProductCard({ product }: { product: (typeof giftProducts)[number] }) {
  return (
    <article className="w-[136px] flex-none rounded-2xl bg-white p-2 shadow-sm ring-1 ring-zinc-100">
      <div className={`grid h-20 place-items-center rounded-xl bg-gradient-to-br ${product.tone}`}>
        <span className="text-4xl">{product.icon}</span>
      </div>
      <h4 className="mt-2 text-[13px] font-black text-zinc-950">{product.name}</h4>
      <div className="mt-0.5 text-[16px] font-black text-[#e93b3d]">{product.price}</div>
      <div className="mt-1 flex flex-wrap gap-1">
        {product.tags.map((tag) => (
          <span key={tag} className="rounded-full bg-violet-50 px-1.5 py-0.5 text-[9px] font-black text-violet-600">
            {tag}
          </span>
        ))}
      </div>
      <p className="mt-1.5 line-clamp-2 min-h-8 text-[10px] font-medium leading-4 text-zinc-500">{product.reason}</p>
      <button className="mt-2 h-7 w-full rounded-full bg-[#e93b3d] text-[11px] font-black text-white">加入礼单</button>
    </article>
  );
}

function AiBubble({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-2">
      <span className="grid h-7 w-7 flex-none place-items-center rounded-full bg-gradient-to-br from-sky-300 via-violet-300 to-pink-300 text-[10px] font-black text-white shadow-[0_6px_16px_rgba(124,58,237,0.22)]">
        AI
      </span>
      <div className="max-w-[285px] rounded-2xl rounded-tl-md bg-white px-3 py-2 text-[13px] font-medium leading-5 text-zinc-800 shadow-sm ring-1 ring-zinc-100">
        {children}
      </div>
    </div>
  );
}

function UserBubble({ children }: { children: ReactNode }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[265px] rounded-2xl rounded-tr-md bg-gradient-to-r from-[#e93b3d] to-red-500 px-3 py-2 text-[13px] font-bold leading-5 text-white shadow-[0_8px_18px_rgba(233,59,61,0.18)]">
        {children}
      </div>
    </div>
  );
}

function JingliPage() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col overflow-hidden bg-gradient-to-b from-[#fff5f5] via-[#f6f7fb] to-[#f1f2f4]">
      <StatusBar />
      <header className="flex h-[58px] flex-none items-center border-b border-zinc-200/70 bg-white/82 px-3 backdrop-blur">
        <button onClick={() => navigate('/home')} className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-2xl font-light text-zinc-800">
          ‹
        </button>
        <div className="min-w-0 flex-1 text-center">
          <h1 className="text-[16px] font-black text-zinc-950">京礼 AI 送礼助手</h1>
          <p className="mt-0.5 text-[11px] font-bold text-zinc-500">懂关系、懂场景、懂预算</p>
        </div>
        <div className="flex h-8 items-center gap-1 rounded-full bg-violet-50 px-2 text-[11px] font-black text-violet-700 ring-1 ring-violet-100">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)]" />
          在线
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-3 pb-24 pt-3">
        <section className="relative overflow-hidden rounded-[22px] bg-gradient-to-br from-white via-violet-50 to-pink-50 p-3 shadow-sm ring-1 ring-white">
          <div className="absolute right-4 top-3 h-16 w-16 rounded-full bg-violet-200/40 blur-2xl" />
          <div className="relative flex gap-3">
            <div className="grid h-[52px] w-[52px] flex-none place-items-center rounded-2xl bg-gradient-to-br from-sky-300 via-violet-400 to-pink-300 text-2xl shadow-[0_10px_24px_rgba(124,58,237,0.24)]">
              ✨
            </div>
            <div>
              <h2 className="text-[17px] font-black text-zinc-950">你好，我是京礼</h2>
              <p className="mt-1 text-[12px] font-medium leading-5 text-zinc-600">
                告诉我送礼对象、场景和预算，我来帮你挑一份更合适的礼物。
              </p>
            </div>
          </div>
        </section>

        <section className="mt-3">
          <div className="flex items-end justify-between">
            <div>
              <h2 className="text-[16px] font-black text-zinc-950">常见送礼场景</h2>
              <p className="mt-0.5 text-[11px] font-bold text-zinc-500">不知道怎么问？可以先从这些场景开始</p>
            </div>
            <span className="rounded-full bg-red-50 px-2 py-1 text-[10px] font-black text-[#e93b3d]">场景推荐</span>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {giftScenes.map((scene) => (
              <article
                key={scene.title}
                className={`flex gap-2 rounded-2xl p-2 shadow-sm ${
                  scene.active ? 'bg-red-50 ring-1 ring-red-300' : 'bg-white ring-1 ring-zinc-100'
                }`}
              >
                <span className="grid h-9 w-9 flex-none place-items-center rounded-xl bg-white text-xl shadow-sm">{scene.icon}</span>
                <div className="min-w-0">
                  <h3 className={`text-[13px] font-black ${scene.active ? 'text-[#e93b3d]' : 'text-zinc-950'}`}>{scene.title}</h3>
                  <p className="mt-0.5 truncate text-[10px] font-bold text-zinc-500">{scene.desc}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-3 space-y-3">
          <AiBubble>
            你好，我是京礼。你可以告诉我：送给谁、什么场景、预算多少，我会帮你推荐更合适的礼物。
          </AiBubble>
          <UserBubble>想给25岁女生送生日礼物，预算500元。</UserBubble>
          <AiBubble>
            这个场景建议选择有心意、颜值高、不过度昂贵的礼物。可以优先考虑香氛礼盒、小家电、美妆护肤或精致数码配件。
          </AiBubble>
        </section>

        <section className="mt-3 rounded-[22px] bg-white/72 p-3 shadow-sm ring-1 ring-white backdrop-blur">
          <div className="flex items-center justify-between">
            <h2 className="text-[16px] font-black text-zinc-950">京礼为你推荐</h2>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-600">预算 ¥500 内</span>
          </div>
          <div className="no-scrollbar mt-2 flex gap-2 overflow-x-auto pb-1">
            {giftProducts.map((product) => (
              <GiftProductCard key={product.name} product={product} />
            ))}
          </div>
          <button
            onClick={() => navigate('/combo-chat')}
            className="mt-2 h-9 w-full rounded-full bg-gradient-to-r from-[#e93b3d] to-violet-500 text-[12px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.18)]"
          >
            试试复杂送礼组合
          </button>
        </section>

        <section className="mt-3">
          <h2 className="text-[15px] font-black text-zinc-950">你还可以这样问</h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {quickQuestions.map((question) => (
              <span key={question} className="rounded-full bg-white px-3 py-2 text-[12px] font-bold text-zinc-700 shadow-sm ring-1 ring-zinc-100">
                {question}
              </span>
            ))}
          </div>
        </section>
      </div>

      <div className="h-[76px] flex-none border-t border-zinc-200 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.05)]">
        <div className="flex h-11 items-center gap-2">
          <button className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-xl font-light text-zinc-700">＋</button>
          <div className="flex h-10 flex-1 items-center rounded-full bg-zinc-100 px-3 text-[13px] font-medium text-zinc-400">
            说说你想送给谁、预算多少
          </div>
          <button className="h-10 rounded-full bg-[#e93b3d] px-4 text-[13px] font-black text-white shadow-[0_8px_16px_rgba(233,59,61,0.18)]">
            发送
          </button>
        </div>
      </div>
    </div>
  );
}

function ComboPreviewProduct({ product }: { product: (typeof comboProducts)[number] }) {
  return (
    <div className="rounded-2xl bg-zinc-50 p-2">
      <div className={`grid h-12 place-items-center rounded-xl bg-gradient-to-br ${product.tone}`}>
        <span className="text-2xl">{product.icon}</span>
      </div>
      <h4 className="mt-1.5 truncate text-[11px] font-black text-zinc-900">{product.name}</h4>
      <div className="mt-0.5 text-[13px] font-black text-[#e93b3d]">{product.price}</div>
    </div>
  );
}

function ComboChatPage() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col overflow-hidden bg-gradient-to-b from-[#fff5f5] via-[#f6f7fb] to-[#f1f2f4]">
      <StatusBar />
      <header className="flex h-[58px] flex-none items-center border-b border-zinc-200/70 bg-white/82 px-3 backdrop-blur">
        <button onClick={() => navigate('/jingli')} className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-2xl font-light text-zinc-800">
          ‹
        </button>
        <div className="min-w-0 flex-1 text-center">
          <h1 className="text-[16px] font-black text-zinc-950">京礼 AI 送礼助手</h1>
          <p className="mt-0.5 text-[11px] font-bold text-zinc-500">正在为你规划组合礼单</p>
        </div>
        <div className="flex h-8 items-center gap-1 rounded-full bg-violet-50 px-2 text-[11px] font-black text-violet-700 ring-1 ring-violet-100">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)]" />
          AI 在线
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-3 pb-24 pt-3">
        <section className="relative overflow-hidden rounded-[22px] bg-gradient-to-br from-violet-50 via-white to-red-50 p-3 shadow-sm ring-1 ring-white">
          <div className="absolute right-4 top-4 h-16 w-16 rounded-full bg-violet-200/40 blur-2xl" />
          <div className="relative flex items-center gap-2">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-sky-300 via-violet-400 to-pink-300 text-xl shadow-[0_8px_18px_rgba(124,58,237,0.22)]">✨</span>
            <div className="min-w-0">
              <h2 className="text-[15px] font-black text-zinc-950">已识别送礼条件</h2>
              <p className="mt-1 text-[12px] font-bold leading-5 text-zinc-600">长辈关系｜预算3000｜正式送礼｜适合组合方案</p>
            </div>
          </div>
        </section>

        <section className="mt-3 space-y-3">
          <AiBubble>你好，我是京礼。复杂送礼场景我可以帮你生成组合方案。</AiBubble>
          <UserBubble>给老丈人送礼，预算3000元左右，想体面一点。</UserBubble>
          <AiBubble>
            这个场景不建议只推荐单个商品。给长辈或老丈人送礼，更适合组合礼单，可以同时兼顾体面感、健康关怀、家庭共享和实用价值。
          </AiBubble>
        </section>

        <section className="mt-3 overflow-hidden rounded-[24px] bg-white p-3 shadow-sm ring-1 ring-zinc-100">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-[18px] font-black text-zinc-950">老丈人见面礼组合</h2>
              <p className="mt-0.5 text-[12px] font-bold text-zinc-500">
                预算 <span className="text-[#e93b3d]">¥3000</span>｜当前组合 <span className="text-[#e93b3d]">¥2986</span>｜剩余 ¥14
              </p>
            </div>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-700">AI 组合推荐</span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {comboProducts.map((product) => (
              <ComboPreviewProduct key={product.name} product={product} />
            ))}
          </div>
          <div className="mt-3 grid gap-1.5">
            {['体面感：正式拜访不显随意', '健康关怀：更适合长辈关系', '家庭共享：让礼物更自然'].map((item) => (
              <div key={item} className="rounded-full bg-red-50 px-3 py-1.5 text-[11px] font-black text-[#e93b3d]">
                {item}
              </div>
            ))}
          </div>
          <button
            onClick={() => navigate('/combo-plan')}
            className="mt-3 h-10 w-full rounded-full bg-gradient-to-r from-[#e93b3d] to-violet-500 text-[13px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.2)]"
          >
            查看完整组合礼单
          </button>
        </section>
      </div>

      <div className="h-[76px] flex-none border-t border-zinc-200 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.05)]">
        <div className="flex h-11 items-center gap-2">
          <button className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-xl font-light text-zinc-700">＋</button>
          <div className="flex h-10 flex-1 items-center rounded-full bg-zinc-100 px-3 text-[13px] font-medium text-zinc-400">
            继续补充他的喜好或忌口
          </div>
          <button className="h-10 rounded-full bg-[#e93b3d] px-4 text-[13px] font-black text-white shadow-[0_8px_16px_rgba(233,59,61,0.18)]">
            发送
          </button>
        </div>
      </div>
    </div>
  );
}

function ComboProductRow({ product }: { product: (typeof comboProducts)[number] }) {
  return (
    <article className="flex gap-3 border-b border-zinc-100 py-3 last:border-b-0">
      <div className={`grid h-[68px] w-[68px] flex-none place-items-center rounded-2xl bg-gradient-to-br ${product.tone} shadow-sm`}>
        <span className="text-3xl">{product.icon}</span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-[14px] font-black leading-5 text-zinc-950">{product.name}</h3>
          <span className="flex-none text-[16px] font-black text-[#e93b3d]">{product.price}</span>
        </div>
        <div className="mt-1 flex flex-wrap gap-1">
          {product.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-red-50 px-2 py-0.5 text-[9px] font-black text-[#e93b3d]">
              {tag}
            </span>
          ))}
        </div>
        <p className="mt-1 text-[11px] font-medium leading-4 text-zinc-500">{product.reason}</p>
      </div>
    </article>
  );
}

function GiftComboPlanPage() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col overflow-hidden bg-gradient-to-b from-[#fff5f3] via-[#f6f7fb] to-[#f1f2f4]">
      <StatusBar />
      <header className="flex h-[58px] flex-none items-center border-b border-zinc-200/70 bg-white/85 px-3 backdrop-blur">
        <button onClick={() => navigate('/combo-chat')} className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-2xl font-light text-zinc-800">
          ‹
        </button>
        <div className="min-w-0 flex-1 text-center">
          <h1 className="text-[16px] font-black text-zinc-950">京礼组合礼单</h1>
          <p className="mt-0.5 text-[11px] font-bold text-zinc-500">AI 为你生成送礼方案</p>
        </div>
        <div className="flex h-8 items-center gap-1 rounded-full bg-violet-50 px-2 text-[11px] font-black text-violet-700 ring-1 ring-violet-100">
          <span className="h-2 w-2 rounded-full bg-violet-400 shadow-[0_0_10px_rgba(139,92,246,0.8)]" />
          AI 推荐
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-3 pb-24 pt-3">
        <div className="mb-2 flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-50 via-white to-red-50 px-3 py-2 text-[12px] font-black text-violet-700 shadow-sm ring-1 ring-white">
          <span>✨</span>
          AI 已根据关系、预算、场景生成组合方案
        </div>

        <section className="rounded-[22px] bg-white p-3 shadow-sm ring-1 ring-zinc-100">
          <div className="flex items-center gap-2">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-red-50 text-2xl">🤝</span>
            <div>
              <h2 className="text-[17px] font-black text-zinc-950">送礼需求</h2>
              <p className="text-[11px] font-bold text-zinc-500">给老丈人送礼，预算 3000 元左右，想体面一点</p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {[
              ['送礼对象', '老丈人'],
              ['预算范围', '¥3000 左右'],
              ['送礼目标', '体面、稳妥、有心意'],
              ['关系阶段', '正式拜访 / 建立好印象'],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-zinc-50 px-2.5 py-2">
                <div className="text-[10px] font-black text-zinc-400">{label}</div>
                <div className={`mt-0.5 text-[12px] font-black ${value.includes('¥') ? 'text-[#e93b3d]' : 'text-zinc-800'}`}>{value}</div>
              </div>
            ))}
          </div>
          <div className="mt-2 rounded-2xl bg-red-50 px-3 py-2 text-[12px] font-black text-[#e93b3d]">推荐策略：组合礼单，而不是单一商品</div>
        </section>

        <section className="relative mt-3 overflow-hidden rounded-[22px] bg-gradient-to-br from-sky-50 via-violet-50 to-white p-3 shadow-sm ring-1 ring-white">
          <div className="absolute right-5 top-4 h-20 w-20 rounded-full bg-violet-200/40 blur-2xl" />
          <div className="relative flex items-start gap-2">
            <span className="grid h-9 w-9 flex-none place-items-center rounded-2xl bg-gradient-to-br from-sky-300 to-violet-400 text-xl shadow-[0_8px_18px_rgba(124,58,237,0.2)]">✨</span>
            <div>
              <h2 className="text-[16px] font-black text-zinc-950">为什么推荐组合礼单？</h2>
              <p className="mt-1 text-[12px] font-medium leading-5 text-zinc-600">
                给长辈或老丈人送礼，单件商品容易显得单薄。组合礼单可以同时覆盖体面感、健康关怀、家庭共享和实用价值，更适合正式送礼场景。
              </p>
            </div>
          </div>
          <div className="relative mt-2 flex gap-2">
            {['体面不出错', '健康有心意', '全家可共享'].map((tag) => (
              <span key={tag} className="rounded-full bg-white/80 px-2 py-1 text-[10px] font-black text-violet-700 ring-1 ring-violet-100">
                {tag}
              </span>
            ))}
          </div>
        </section>

        <section className="mt-3 rounded-[24px] bg-white p-3 shadow-sm ring-1 ring-zinc-100">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-[18px] font-black text-zinc-950">老丈人见面礼组合</h2>
              <p className="mt-0.5 text-[12px] font-bold text-zinc-500">预算 <span className="text-[#e93b3d]">¥3000</span>｜当前组合 <span className="text-[#e93b3d]">¥2986</span>｜剩余 ¥14</p>
            </div>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-700">AI 组合推荐</span>
          </div>
          <div className="mt-3 rounded-2xl bg-zinc-50 p-3">
            <div className="flex items-center justify-between text-[11px] font-black text-zinc-500">
              <span>总预算 ¥3000</span>
              <span className="text-[#e93b3d]">99.5%</span>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-white">
              <div className="h-full w-[99.5%] rounded-full bg-gradient-to-r from-[#e93b3d] via-red-500 to-violet-500" />
            </div>
            <div className="mt-2 flex justify-between text-[10px] font-bold text-zinc-500">
              <span>已使用 ¥2986</span>
              <span>剩余 ¥14</span>
            </div>
          </div>
        </section>

        <section className="mt-3 rounded-[22px] bg-white px-3 shadow-sm ring-1 ring-zinc-100">
          {comboProducts.map((product) => (
            <ComboProductRow key={product.name} product={product} />
          ))}
        </section>

        <section className="mt-3">
          <h2 className="text-[16px] font-black text-zinc-950">为什么这样搭配？</h2>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {valuePoints.map((point) => (
              <article key={point.title} className={`rounded-2xl p-2 ${point.tone}`}>
                <div className="text-xl">{point.icon}</div>
                <h3 className="mt-1 text-[12px] font-black">{point.title}</h3>
                <p className="mt-1 text-[10px] font-bold leading-4 opacity-80">{point.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-3">
          <h2 className="text-[16px] font-black text-zinc-950">可替换方向</h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {comboChips.map((chip) => (
              <button
                key={chip}
                onClick={() => chip === '更高端' && navigate('/combo-premium')}
                className={`rounded-full px-3 py-2 text-[12px] font-black shadow-sm ring-1 ${
                  chip === '更高端' ? 'bg-violet-50 text-violet-700 ring-violet-100' : 'bg-white text-zinc-700 ring-zinc-100'
                }`}
              >
                {chip}
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="h-[76px] flex-none border-t border-zinc-200 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.05)]">
        <div className="flex h-11 gap-2">
          <button className="flex-1 rounded-full border border-[#e93b3d] bg-white text-[13px] font-black text-[#e93b3d]">换一套组合</button>
          <button onClick={() => navigate('/cart')} className="flex-[1.35] rounded-full bg-[#e93b3d] text-[13px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.2)]">一键加入礼单</button>
        </div>
      </div>
    </div>
  );
}

function PremiumComboPlanPage() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col overflow-hidden bg-gradient-to-b from-[#fff4ee] via-[#f7f2fb] to-[#f1f2f4]">
      <StatusBar />
      <header className="flex h-[58px] flex-none items-center border-b border-zinc-200/70 bg-white/85 px-3 backdrop-blur">
        <button onClick={() => navigate('/combo-plan')} className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-2xl font-light text-zinc-800">‹</button>
        <div className="min-w-0 flex-1 text-center">
          <h1 className="text-[16px] font-black text-zinc-950">高端组合礼单</h1>
          <p className="mt-0.5 text-[11px] font-bold text-zinc-500">AI 已为你升级方案</p>
        </div>
        <div className="rounded-full bg-gradient-to-r from-amber-100 to-violet-100 px-2.5 py-1.5 text-[11px] font-black text-violet-700 ring-1 ring-violet-100">高端版</div>
      </header>

      <div className="flex-1 overflow-y-auto px-3 pb-24 pt-3">
        <div className="mb-2 rounded-full bg-gradient-to-r from-violet-50 via-white to-amber-50 px-3 py-2 text-[12px] font-black text-violet-700 shadow-sm ring-1 ring-white">
          ✨ 已根据“更高端”偏好重新生成方案
        </div>

        <section className="rounded-[22px] bg-white p-3 shadow-sm ring-1 ring-zinc-100">
          <div className="flex items-center gap-2">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-amber-50 text-2xl">🎁</span>
            <div>
              <h2 className="text-[17px] font-black text-zinc-950">升级需求</h2>
              <p className="text-[11px] font-bold text-zinc-500">老丈人见面礼，从体面升级到更有分量</p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {[
              ['送礼对象', '老丈人'],
              ['原预算', '¥3000 左右'],
              ['新策略', '提高体面感与品质感'],
              ['方案类型', '高端组合礼单'],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-zinc-50 px-2.5 py-2">
                <div className="text-[10px] font-black text-zinc-400">{label}</div>
                <div className={`mt-0.5 text-[12px] font-black ${value.includes('¥') ? 'text-[#e93b3d]' : 'text-zinc-800'}`}>{value}</div>
              </div>
            ))}
          </div>
          <div className="mt-2 rounded-2xl bg-red-50 px-3 py-2 text-[12px] font-black text-[#e93b3d]">推荐目标：正式、稳妥、有分量</div>
        </section>

        <section className="relative mt-3 overflow-hidden rounded-[22px] bg-gradient-to-br from-amber-50 via-violet-50 to-white p-3 shadow-sm ring-1 ring-white">
          <div className="absolute right-5 top-4 h-20 w-20 rounded-full bg-amber-200/40 blur-2xl" />
          <div className="relative flex items-start gap-2">
            <span className="grid h-9 w-9 flex-none place-items-center rounded-2xl bg-gradient-to-br from-amber-300 to-violet-400 text-xl shadow-[0_8px_18px_rgba(124,58,237,0.2)]">✨</span>
            <div>
              <h2 className="text-[16px] font-black text-zinc-950">为什么升级？</h2>
              <p className="mt-1 text-[12px] font-medium leading-5 text-zinc-600">
                正式拜访长辈时，礼物不只要实用，也要体现诚意和分寸。高端版方案会提升主礼品质，同时保留健康关怀和家庭共享属性。
              </p>
            </div>
          </div>
          <div className="relative mt-2 flex gap-2">
            {['更体面', '更高端', '更有分量'].map((tag) => (
              <span key={tag} className="rounded-full bg-white/80 px-2 py-1 text-[10px] font-black text-violet-700 ring-1 ring-violet-100">{tag}</span>
            ))}
          </div>
        </section>

        <section className="mt-3 rounded-[24px] bg-white p-3 shadow-sm ring-1 ring-zinc-100">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-[18px] font-black text-zinc-950">老丈人见面礼组合 · 高端版</h2>
              <p className="mt-0.5 text-[12px] font-bold text-zinc-500">预算 <span className="text-[#e93b3d]">¥5000</span>｜当前组合 <span className="text-[#e93b3d]">¥4968</span>｜剩余 ¥32</p>
            </div>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-700">AI 高端推荐</span>
          </div>
          <div className="mt-3 rounded-2xl bg-zinc-50 p-3">
            <div className="flex items-center justify-between text-[11px] font-black text-zinc-500">
              <span>总预算 ¥5000</span>
              <span className="text-[#e93b3d]">99.4%</span>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-white">
              <div className="h-full w-[99.4%] rounded-full bg-gradient-to-r from-[#e93b3d] via-amber-500 to-violet-500" />
            </div>
            <div className="mt-2 flex justify-between text-[10px] font-bold text-zinc-500">
              <span>已使用 ¥4968</span>
              <span>剩余 ¥32</span>
            </div>
          </div>
        </section>

        <section className="mt-3 rounded-[22px] bg-white px-3 shadow-sm ring-1 ring-zinc-100">
          {premiumProducts.map((product) => (
            <ComboProductRow key={product.name} product={product} />
          ))}
          <div className="border-t border-zinc-100 py-3 text-right text-[15px] font-black text-[#e93b3d]">合计 ¥4968</div>
        </section>

        <section className="mt-3">
          <h2 className="text-[16px] font-black text-zinc-950">为什么这样搭配？</h2>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {premiumValuePoints.map((point) => (
              <article key={point.title} className={`rounded-2xl p-2 ${point.tone}`}>
                <div className="text-xl">{point.icon}</div>
                <h3 className="mt-1 text-[12px] font-black">{point.title}</h3>
                <p className="mt-1 text-[10px] font-bold leading-4 opacity-80">{point.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-3">
          <h2 className="text-[16px] font-black text-zinc-950">可替换方向</h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {premiumChips.map((chip) => (
              <span key={chip} className="rounded-full bg-white px-3 py-2 text-[12px] font-black text-zinc-700 shadow-sm ring-1 ring-zinc-100">{chip}</span>
            ))}
          </div>
        </section>
      </div>

      <div className="h-[76px] flex-none border-t border-zinc-200 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.05)]">
        <div className="flex h-11 gap-2">
          <button onClick={() => navigate('/combo-plan')} className="flex-1 rounded-full border border-[#e93b3d] bg-white text-[13px] font-black text-[#e93b3d]">返回原方案</button>
          <button onClick={() => navigate('/cart')} className="flex-[1.35] rounded-full bg-[#e93b3d] text-[13px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.2)]">一键加入礼单</button>
        </div>
      </div>
    </div>
  );
}

function CartTabBar() {
  const navigate = useNavigate();

  return (
    <div className="h-[58px] flex-none border-t border-zinc-200 bg-white px-2 pt-1.5">
      <div className="grid grid-cols-5">
        {bottomTabs.map((tab, index) => (
          <button
            key={tab}
            onClick={() => tab === '首页' && navigate('/home')}
            className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${tab === '购物车' ? 'text-[#e93b3d]' : 'text-zinc-500'}`}
          >
            <span className={`relative grid h-6 w-6 place-items-center rounded-full ${tab === '购物车' ? 'bg-[#e93b3d] text-white' : 'bg-zinc-100 text-zinc-600'}`}>
              {['⌂', '◇', '✉', '🛒', '☺'][index]}
              {(tab === '消息' || tab === '购物车') && (
                <span className="absolute -right-1 -top-0.5 grid h-3.5 min-w-3.5 place-items-center rounded-full bg-[#e93b3d] px-0.5 text-[8px] font-black leading-none text-white">2</span>
              )}
            </span>
            {tab}
          </button>
        ))}
      </div>
    </div>
  );
}

function CartProductRow({ product }: { product: (typeof cartProducts)[number] }) {
  return (
    <article className="flex gap-2 border-b border-zinc-100 py-3 last:border-b-0">
      <span className="mt-6 h-4 w-4 flex-none rounded-full bg-[#e93b3d] text-center text-[10px] leading-4 text-white">✓</span>
      <div className={`grid h-[72px] w-[72px] flex-none place-items-center rounded-2xl bg-gradient-to-br ${product.tone}`}>
        <span className="text-3xl">{product.icon}</span>
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="truncate text-[13px] font-black text-zinc-950">{product.name}</h3>
        <p className="mt-0.5 truncate text-[10px] font-bold text-zinc-500">{product.spec}</p>
        <div className="mt-1 flex flex-wrap gap-1">
          {product.tags.map((tag) => (
            <span key={tag} className="rounded bg-red-50 px-1.5 py-0.5 text-[9px] font-black text-[#e93b3d]">{tag}</span>
          ))}
        </div>
        <div className="mt-1.5 flex items-end justify-between">
          <span className="text-[16px] font-black text-[#e93b3d]">{product.price}</span>
          <div className="flex h-6 items-center overflow-hidden rounded-full border border-zinc-200 text-[11px] font-black">
            <span className="px-2 text-zinc-400">-</span>
            <span className="bg-zinc-50 px-2 text-zinc-800">1</span>
            <span className="px-2 text-zinc-700">+</span>
          </div>
        </div>
      </div>
    </article>
  );
}

function GiftCartPage() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#f3f4f7]">
      <StatusBar />
      <header className="flex h-[52px] flex-none items-center bg-white px-3">
        <button onClick={() => navigate('/combo-plan')} className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-2xl font-light text-zinc-800">‹</button>
        <h1 className="flex-1 text-center text-[18px] font-black text-zinc-950">购物车（4）</h1>
        <div className="flex items-center gap-3 text-[13px] font-bold text-zinc-700">
          <span>管理</span>
          <span>•••</span>
        </div>
      </header>

      <div className="flex h-9 flex-none items-center gap-7 bg-white px-4 text-[13px] font-black text-zinc-600">
        {['全部', '购物', '秒送', '服务'].map((tab) => (
          <span key={tab} className={`relative h-full pt-2 ${tab === '全部' ? 'text-[#e93b3d]' : ''}`}>
            {tab}
            {tab === '全部' && <span className="absolute bottom-0 left-1/2 h-1 w-5 -translate-x-1/2 rounded-full bg-[#e93b3d]" />}
          </span>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-28 pt-2">
        <div className="no-scrollbar flex gap-2 overflow-x-auto text-[11px] font-black">
          {['京礼礼单', '国家补贴', '送礼', '分组', '筛选'].map((tag) => (
            <span key={tag} className="rounded-full bg-white px-3 py-1.5 text-zinc-700 shadow-sm">{tag}</span>
          ))}
        </div>
        <div className="mt-2 rounded-2xl bg-gradient-to-r from-violet-50 to-red-50 px-3 py-2 text-[12px] font-black text-violet-700 shadow-sm">
          ✨ 京礼已为你加入 4 件商品，组成老丈人见面礼组合
        </div>

        <section className="mt-2 rounded-[22px] bg-white px-3 shadow-sm">
          <div className="flex items-center border-b border-zinc-100 py-3">
            <span className="mr-2 h-4 w-4 rounded-full bg-[#e93b3d] text-center text-[10px] leading-4 text-white">✓</span>
            <h2 className="flex-1 text-[14px] font-black text-zinc-950">京礼精选组合</h2>
            <span className="text-zinc-400">›</span>
          </div>
          {cartProducts.map((product) => (
            <CartProductRow key={product.name} product={product} />
          ))}
        </section>

        <section className="mt-2 rounded-[22px] bg-white p-3 shadow-sm">
          <h2 className="text-[15px] font-black text-zinc-950">你可能还需要</h2>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {[
              ['贺卡', '¥29', '💌'],
              ['礼品袋', '¥19', '🛍️'],
            ].map(([name, price, icon]) => (
              <div key={name} className="flex items-center gap-2 rounded-2xl bg-zinc-50 p-2">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-white text-2xl">{icon}</span>
                <div>
                  <div className="text-[12px] font-black text-zinc-900">{name}</div>
                  <div className="text-[14px] font-black text-[#e93b3d]">{price}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="h-[62px] flex-none border-t border-zinc-200 bg-white px-3 pt-2">
        <div className="flex h-10 items-center gap-2">
          <div className="flex items-center gap-1 text-[12px] font-black text-zinc-700">
            <span className="h-4 w-4 rounded-full bg-[#e93b3d] text-center text-[10px] leading-4 text-white">✓</span>
            全选
          </div>
          <div className="min-w-0 flex-1 text-right">
            <div className="text-[12px] font-bold text-zinc-600">合计：<span className="text-[18px] font-black text-[#e93b3d]">¥2986</span></div>
            <div className="text-[10px] font-bold text-zinc-400">共 4 件｜已优惠 ¥214</div>
          </div>
          <button className="h-10 rounded-full bg-[#e93b3d] px-4 text-[13px] font-black text-white shadow-[0_8px_16px_rgba(233,59,61,0.2)]">去结算（4）</button>
        </div>
      </div>
      <CartTabBar />
    </div>
  );
}

function LegacyHomePage() {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <StatusBar />
      <TopNav />
      <SearchBar />
      <ChannelBar />
      <div className="flex-1 overflow-y-auto pb-3">
        <GiftComboEntryCard />
        <ShortcutGrid />
        <FeatureGrid />
        <PromoBanner />
        <BottomAdGrid />
      </div>
      <BottomTabBar />
    </div>
  );
}

function AiMascot() {
  return (
    <div className="relative h-[136px] w-[132px]">
      <div className="absolute right-1 top-4 h-24 w-24 rounded-[34px] bg-gradient-to-br from-white via-violet-100 to-sky-100 shadow-[0_18px_38px_rgba(124,58,237,0.18)] ring-1 ring-white" />
      <div className="absolute right-7 top-11 flex gap-4">
        <span className="h-2.5 w-2.5 rounded-full bg-violet-500" />
        <span className="h-2.5 w-2.5 rounded-full bg-violet-500" />
      </div>
      <div className="absolute right-10 top-[70px] h-2 w-9 rounded-full bg-violet-300" />
      <div className="absolute right-20 top-0 rounded-full bg-white px-2 py-1 text-sm shadow-sm">✨</div>
      <div className="absolute bottom-2 left-2 rounded-[26px] bg-gradient-to-br from-violet-200 to-pink-100 px-4 py-3 text-2xl shadow-[0_12px_30px_rgba(124,58,237,0.16)]">AI</div>
      <div className="absolute bottom-8 right-0 h-9 w-9 rounded-full bg-white/90 shadow-sm" />
    </div>
  );
}

function ServiceCard({
  title,
  desc,
  icon,
  tone,
  onClick,
}: {
  title: string;
  desc: string;
  icon: string;
  tone: string;
  onClick?: () => void;
}) {
  return (
    <button onClick={onClick} className="flex min-h-[86px] items-center gap-2 rounded-2xl bg-white p-3 text-left shadow-sm ring-1 ring-zinc-100 transition active:scale-[0.99]">
      <span className={`grid h-10 w-10 flex-none place-items-center rounded-2xl bg-gradient-to-br ${tone} text-xl shadow-sm`}>{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="block text-[14px] font-black text-zinc-950">{title}</span>
        <span className="mt-1 block text-[11px] font-bold leading-4 text-zinc-500">{desc}</span>
      </span>
      <span className="text-lg font-light text-zinc-300">›</span>
    </button>
  );
}

function HomePage() {
  const navigate = useNavigate();
  const questions = ['如何挑选防晒衣更凉爽？', '🥬 春菜忌忙，荠菜怎么调鲜？', '👁️ 过敏眼痒，洗眼液能天天用？'];

  return (
    <div className="flex h-full flex-col overflow-hidden bg-gradient-to-b from-[#faf8ff] via-[#f7f7fb] to-[#f1f2f5]">
      <div className="flex h-8 items-center justify-between px-5 text-[13px] font-semibold text-zinc-950">
        <span>21:09</span>
        <div className="flex items-center gap-1.5">
          <div className="flex h-3.5 items-end gap-0.5">
            <span className="block h-1.5 w-1 rounded-sm bg-zinc-900" />
            <span className="block h-2 w-1 rounded-sm bg-zinc-900" />
            <span className="block h-2.5 w-1 rounded-sm bg-zinc-900" />
            <span className="block h-3 w-1 rounded-sm bg-zinc-900" />
          </div>
          <span className="text-[11px]">5G</span>
          <div className="flex h-3.5 w-6 items-center rounded-[4px] border border-zinc-900 p-0.5">
            <span className="h-full w-4 rounded-[2px] bg-zinc-900" />
          </div>
        </div>
      </div>

      <header className="flex h-12 flex-none items-center gap-2 px-3">
        <button className="grid h-9 w-9 place-items-center rounded-full bg-white/80 text-2xl font-light text-zinc-800 shadow-sm">‹</button>
        <div className="flex h-9 min-w-0 flex-1 items-center justify-center gap-1 rounded-full bg-white px-3 text-[12px] font-black text-zinc-800 shadow-sm ring-1 ring-zinc-100">
          <span className="text-violet-500">⌖</span>
          <span className="truncate">京东集团全球培训基地</span>
          <span className="text-zinc-400">⌄</span>
        </div>
        <button className="grid h-9 w-9 place-items-center rounded-full bg-white text-lg shadow-sm">💬</button>
        <button className="relative grid h-9 w-9 place-items-center rounded-full bg-white text-lg shadow-sm">
          🛒
          <span className="absolute -right-1 -top-1 rounded-full bg-violet-500 px-1 text-[8px] font-black text-white">99+</span>
        </button>
        <button className="grid h-9 w-9 place-items-center rounded-full bg-white text-lg shadow-sm">☰</button>
      </header>

      <div className="flex-1 overflow-y-auto px-3 pb-24 pt-2">
        <section className="relative min-h-[178px] overflow-hidden rounded-[28px] bg-gradient-to-br from-white via-violet-50 to-sky-50 p-5 shadow-sm ring-1 ring-white">
          <div className="absolute -right-2 top-5">
            <AiMascot />
          </div>
          <div className="relative max-w-[190px] pt-6">
            <p className="text-[34px] font-black leading-10 text-violet-300">生活指令</p>
            <p className="mt-1 text-[28px] font-black leading-9 text-violet-400">京言即刻响应</p>
          </div>
        </section>

        <section className="mt-3 grid grid-cols-2 gap-2">
          <ServiceCard title="AI 帮你买" desc="想买什么，告诉我帮你找" icon="🔎" tone="from-orange-200 to-amber-100" />
          <ServiceCard title="京礼AI" desc="送礼场景，帮你挑好礼" icon="🎁" tone="from-violet-200 to-emerald-100" onClick={() => navigate('/jingli')} />
          <ServiceCard title="AI 省钱" desc="全网好价，帮你划算下单" icon="¥" tone="from-red-200 to-pink-100" />
          <ServiceCard title="AI 试穿" desc="一键上身，还原真实效果" icon="👕" tone="from-pink-200 to-violet-100" />
        </section>

        <section className="mt-5">
          <h2 className="px-1 text-[17px] font-black text-zinc-950">可以这样问我哦~</h2>
          <div className="mt-2 space-y-2">
            {questions.map((question) => (
              <div key={question} className="flex h-12 items-center rounded-2xl bg-white/78 px-4 text-[13px] font-bold text-zinc-800 shadow-sm ring-1 ring-zinc-100">
                <span className="min-w-0 flex-1 truncate">{question}</span>
                <span className="text-xl font-light text-zinc-300">›</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="h-[76px] flex-none border-t border-zinc-200/70 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.04)]">
        <div className="flex h-11 items-center gap-2 rounded-full bg-zinc-100 px-3">
          <div className="flex-1 text-[13px] font-bold text-zinc-400">请输入你的问题</div>
          <button className="grid h-8 w-8 place-items-center rounded-full bg-white text-xl text-zinc-700">＋</button>
          <button className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-violet-400 to-sky-300 text-white">🎙</button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const getViewportHeight = () => Math.floor(window.visualViewport?.height ?? window.innerHeight);
  const [appHeight, setAppHeight] = useState(() => Math.min(844, getViewportHeight()));

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
    const syncHeight = () => setAppHeight(Math.min(844, getViewportHeight()));
    syncHeight();
    const timers = [80, 240, 600].map((delay) => window.setTimeout(syncHeight, delay));
    window.addEventListener('resize', syncHeight);
    window.visualViewport?.addEventListener('resize', syncHeight);
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
      window.removeEventListener('resize', syncHeight);
      window.visualViewport?.removeEventListener('resize', syncHeight);
    };
  }, []);

  return (
    <main className="flex h-screen items-center justify-center overflow-hidden bg-[#f3f4f7] text-zinc-950">
      <section
        className="mx-auto w-[390px] overflow-hidden rounded-[34px] bg-gradient-to-b from-[#fff4f1] via-[#f6f3f2] to-[#f1f2f4] shadow-2xl ring-1 ring-black/5"
        style={{ height: appHeight }}
      >
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/jingli" element={<JingliPage />} />
            <Route path="/combo-chat" element={<ComboChatPage />} />
            <Route path="/combo-plan" element={<GiftComboPlanPage />} />
            <Route path="/combo-premium" element={<PremiumComboPlanPage />} />
            <Route path="/cart" element={<GiftCartPage />} />
            <Route path="/combo" element={<Navigate to="/combo-plan" replace />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        </BrowserRouter>
      </section>
    </main>
  );
}
