import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import type { ProductCardData } from '../api/chat';
import { generateGiftPlan, type GiftPlanResponse } from '../api/giftPlan';
import {
  addGiftListItem,
  getGiftList,
  previewGiftListCheckout,
  removeGiftListItem,
  updateGiftListItemQuantity,
  type GiftListCheckoutPreviewResponse,
  type GiftListResponse,
} from '../api/giftList';
import { bottomTabs, channels, lifeEntries, promoItems, shortcuts, topTabs } from '../data/homeData';
import {
  cartProducts,
  comboChips,
  comboProducts,
  giftProducts,
  giftScenes,
  premiumChips,
  premiumProducts,
  premiumValuePoints,
  quickQuestions,
  valuePoints,
} from '../data/giftData';
import {
  formatAmount,
  formatProductPrice,
  loadGiftPlan,
  saveGiftPlan,
  toAmount,
} from '../utils/giftFormatting';
import { useGiftChat, type GiftRequest } from '../hooks/useGiftChat';

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

function MarkdownText({ text }: { text: string }) {
  const renderInline = (value: string) =>
    value.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={`${part}-${index}`} className="font-black text-zinc-950">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });

  return (
    <div className="space-y-1">
      {text.split('\n').map((line, index) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={`blank-${index}`} className="h-1" />;

        const ordered = trimmed.match(/^(\d+)\.\s*(.*)$/);
        if (ordered) {
          return (
            <p key={`${trimmed}-${index}`} className="flex gap-1.5">
              <span className="font-black text-[#e93b3d]">{ordered[1]}.</span>
              <span className="min-w-0 flex-1">{renderInline(ordered[2])}</span>
            </p>
          );
        }

        const bullet = trimmed.match(/^[-*]\s+(.*)$/);
        if (bullet) {
          return (
            <p key={`${trimmed}-${index}`} className="flex gap-1.5">
              <span className="mt-2 h-1 w-1 flex-none rounded-full bg-[#e93b3d]" />
              <span className="min-w-0 flex-1">{renderInline(bullet[1])}</span>
            </p>
          );
        }

        return <p key={`${trimmed}-${index}`}>{renderInline(trimmed)}</p>;
      })}
    </div>
  );
}

function BackendProductCard({
  product,
  added,
  adding,
  onAdd,
  onRemove,
}: {
  product: ProductCardData;
  added?: boolean;
  adding?: boolean;
  onAdd?: (product: ProductCardData) => void;
  onRemove?: (product: ProductCardData) => void;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  // 接受 http(s) 远程图、/ 开头本地资源、./ 相对路径；其余视为无效，走兜底图标
  const rawImage = product.image_url ?? '';
  const isUsableImage =
    rawImage.startsWith('http://') ||
    rawImage.startsWith('https://') ||
    rawImage.startsWith('/') ||
    rawImage.startsWith('./');
  const absoluteImage = isUsableImage ? rawImage : null;
  const displayName = product.name && product.name.trim() ? product.name : '商品信息待补充';

  const isBusy = !!adding;
  const canInteract = added ? !!onRemove : !!onAdd;
  const handleClick = () => {
    if (isBusy) return;
    if (added) {
      onRemove?.(product);
    } else {
      onAdd?.(product);
    }
  };
  const buttonLabel = isBusy
    ? added
      ? '移除中'
      : '加入中'
    : added
      ? '已加入·点击移除'
      : '加入礼单';
  const buttonClass = added ? 'bg-emerald-500' : 'bg-[#e93b3d]';

  return (
    <article className="w-[148px] flex-none rounded-2xl bg-white p-2 shadow-sm ring-1 ring-zinc-100">
      <div className="grid h-20 place-items-center overflow-hidden rounded-xl bg-gradient-to-br from-sky-50 via-violet-50 to-red-50">
        {absoluteImage && !imageFailed ? (
          <img src={absoluteImage} alt={displayName} className="h-full w-full object-cover" onError={() => setImageFailed(true)} />
        ) : (
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white text-2xl shadow-sm">🎁</span>
        )}
      </div>
      <h4 className="mt-2 line-clamp-2 min-h-8 text-[12px] font-black leading-4 text-zinc-950">{displayName}</h4>
      <div className="mt-0.5 text-[16px] font-black text-[#e93b3d]">{formatProductPrice(product.price)}</div>
      <div className="mt-1 flex min-h-5 flex-wrap gap-1">
        {product.tags.slice(0, 3).map((tag) => (
          <span key={tag} className="rounded-full bg-violet-50 px-1.5 py-0.5 text-[9px] font-black text-violet-600">
            {tag}
          </span>
        ))}
      </div>
      <p className="mt-1.5 line-clamp-3 min-h-12 text-[10px] font-medium leading-4 text-zinc-500">{product.reason}</p>
      <button
        type="button"
        onClick={handleClick}
        disabled={!canInteract || isBusy}
        className={`mt-2 h-7 w-full rounded-full text-[11px] font-black text-white shadow-sm transition active:scale-95 disabled:active:scale-100 ${buttonClass} ${isBusy ? 'opacity-70' : ''}`}
      >
        {buttonLabel}
      </button>
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
        {typeof children === 'string' ? <MarkdownText text={children} /> : children}
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

export function JingliPage() {
  const navigate = useNavigate();
  const {
    activeRequest,
    errorMessage,
    isStreaming,
    lastRequest,
    messages,
    retryLastRequest,
    sendGiftRequest,
  } = useGiftChat();
  const [inputValue, setInputValue] = useState('');
  const [giftListCount, setGiftListCount] = useState(0);
  const [addedProductIds, setAddedProductIds] = useState<Set<string>>(() => new Set());
  const [addingProductId, setAddingProductId] = useState<string | null>(null);
  const [giftListErrorMessage, setGiftListErrorMessage] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // 固定的底部推荐区先保留代码入口，当前不渲染，避免每次 AI 回复后重复出现兜底商品。
  // const recommendedProducts = messages.flatMap((message) => message.products ?? []);

  useEffect(() => {
    void getGiftList()
      .then((giftList) => {
        setGiftListCount(giftList.total_count);
        setAddedProductIds(new Set(giftList.items.map((item) => item.product.product_id)));
      })
      .catch((error) => {
        console.warn('gift list load failed', error);
      });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' });
  }, [messages, isStreaming]);

  async function handleSend(request: GiftRequest) {
    const didSend = await sendGiftRequest(request);
    if (didSend) setInputValue('');
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = inputValue.trim();
    if (!message) return;
    void handleSend({
      source: 'input',
      displayMessage: message,
      requestMessage: message,
    });
  }

  async function handleAddGiftList(product: ProductCardData) {
    if (addingProductId || addedProductIds.has(product.product_id)) return;

    setAddingProductId(product.product_id);
    setGiftListErrorMessage(null);
    try {
      const giftList = await addGiftListItem(product);
      setGiftListCount(giftList.total_count);
      setAddedProductIds(new Set(giftList.items.map((item) => item.product.product_id)));
    } catch (error) {
      console.error(error);
      setGiftListErrorMessage('加入礼单失败，请确认后端礼单接口已启动。');
    } finally {
      setAddingProductId(null);
    }
  }

  async function handleRemoveGiftList(product: ProductCardData) {
    if (addingProductId || !addedProductIds.has(product.product_id)) return;

    setAddingProductId(product.product_id);
    setGiftListErrorMessage(null);
    try {
      const giftList = await removeGiftListItem(product.product_id);
      setGiftListCount(giftList.total_count);
      setAddedProductIds(new Set(giftList.items.map((item) => item.product.product_id)));
    } catch (error) {
      console.error(error);
      setGiftListErrorMessage('移除礼单失败，请重试。');
    } finally {
      setAddingProductId(null);
    }
  }

  async function handleScenePlan(scene: (typeof giftScenes)[number]) {
    if (isStreaming) return;

    const prompt = [
      `送礼场景：${scene.title}`,
      `送礼对象：${scene.target}`,
      `预算：${scene.budget}元左右`,
      `推荐目标：${scene.goal}`,
      `场景说明：${scene.desc}`,
      '请先给出适合当前场景的送礼建议，再推荐商品；如果适合组合礼单，请说明组合思路。',
    ].join('；');

    const displayMessage = `${scene.title}送礼，预算${scene.budget}元左右，想要${scene.goal}。`;
    await handleSend({
      source: 'scene',
      sceneId: scene.title,
      displayMessage,
      requestMessage: prompt,
    });
  }

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
              <button
                key={scene.title}
                type="button"
                onClick={() => void handleScenePlan(scene)}
                disabled={activeRequest?.source === 'scene' && activeRequest.sceneId === scene.title}
                className={`flex gap-2 rounded-2xl p-2 shadow-sm ${
                  scene.active ? 'bg-red-50 ring-1 ring-red-300' : 'bg-white ring-1 ring-zinc-100'
                } text-left transition active:scale-[0.98] disabled:opacity-70`}
              >
                <span className="grid h-9 w-9 flex-none place-items-center rounded-xl bg-white text-xl shadow-sm">{scene.icon}</span>
                <div className="min-w-0">
                  <h3 className={`text-[13px] font-black ${scene.active ? 'text-[#e93b3d]' : 'text-zinc-950'}`}>{scene.title}</h3>
                  <p className="mt-0.5 truncate text-[10px] font-bold text-zinc-500">
                    {activeRequest?.source === 'scene' && activeRequest.sceneId === scene.title ? 'AI 正在生成推荐' : scene.desc}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="mt-3 space-y-3">
          {messages.map((message) =>
            message.role === 'user' ? (
              <UserBubble key={message.id}>{message.content}</UserBubble>
            ) : (
              <div key={message.id} className="space-y-2">
                <AiBubble>
                  {message.content || (
                    <span className="inline-flex items-center gap-1 text-zinc-400">
                      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-400" />
                      正在思考合适的推荐
                    </span>
                  )}
                </AiBubble>
                {!!message.products?.length && (
                  <div className="ml-9 rounded-[22px] bg-white/72 p-2 shadow-sm ring-1 ring-white">
                    <div className="mb-2 flex items-center justify-between px-1">
                      <h3 className="text-[13px] font-black text-zinc-950">AI 智能推荐</h3>
                      <button
                        type="button"
                        onClick={() => navigate('/cart')}
                        className="rounded-full bg-emerald-50 px-2 py-1 text-[9px] font-black text-emerald-600 transition active:scale-95"
                      >
                        礼单 {giftListCount}
                      </button>
                    </div>
                    <div className="no-scrollbar flex gap-2 overflow-x-auto pb-1">
                      {message.products.map((product) => (
                        <BackendProductCard
                          key={product.product_id}
                          product={product}
                          added={addedProductIds.has(product.product_id)}
                          adding={addingProductId === product.product_id}
                          onAdd={(item) => void handleAddGiftList(item)}
                          onRemove={(item) => void handleRemoveGiftList(item)}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ),
          )}
          {(errorMessage || giftListErrorMessage) && (
            <div className="rounded-2xl bg-red-50 px-3 py-2 text-[12px] font-bold text-[#e93b3d]">
              <div>{errorMessage || giftListErrorMessage}</div>
              {errorMessage && lastRequest && (
                <button type="button" onClick={() => void retryLastRequest()} className="mt-1 rounded-full bg-white px-2 py-1 text-[10px] font-black text-[#e93b3d]">
                  重试上一条
                </button>
              )}
            </div>
          )}
          <div ref={bottomRef} />
        </section>

        {/*
        <section className="mt-3 rounded-[22px] bg-white/72 p-3 shadow-sm ring-1 ring-white backdrop-blur">
          <div className="flex items-center justify-between">
            <h2 className="text-[16px] font-black text-zinc-950">京礼为你推荐</h2>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-600">
              {recommendedProducts.length ? `礼单 ${giftListCount}` : '预算 ¥500 内'}
            </span>
          </div>
          <div className="no-scrollbar mt-2 flex gap-2 overflow-x-auto pb-1">
            {recommendedProducts.length
              ? recommendedProducts.map((product) => (
                  <BackendProductCard
                    key={product.product_id}
                    product={product}
                    added={addedProductIds.has(product.product_id)}
                    adding={addingProductId === product.product_id}
                    onAdd={(item) => void handleAddGiftList(item)}
                  />
                ))
              : giftProducts.map((product) => <GiftProductCard key={product.name} product={product} />)}
          </div>
          <button
            onClick={() => navigate('/combo-chat')}
            className="mt-2 h-9 w-full rounded-full bg-gradient-to-r from-[#e93b3d] to-violet-500 text-[12px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.18)]"
          >
            试试复杂送礼组合
          </button>
        </section>
        */}

        <section className="mt-3">
          <h2 className="text-[15px] font-black text-zinc-950">你还可以这样问</h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {quickQuestions.map((question) => (
              <button
                key={question}
                type="button"
                onClick={() =>
                  void handleSend({
                    source: 'quick_question',
                    displayMessage: question,
                    requestMessage: `用户点击快捷问题：${question}。请基于这个送礼需求给出建议并推荐商品。`,
                  })
                }
                className="rounded-full bg-white px-3 py-2 text-[12px] font-bold text-zinc-700 shadow-sm ring-1 ring-zinc-100 transition active:scale-95 disabled:opacity-50"
                disabled={isStreaming}
              >
                {question}
              </button>
            ))}
          </div>
        </section>
      </div>

      <form onSubmit={handleSubmit} className="h-[76px] flex-none border-t border-zinc-200 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.05)]">
        <div className="flex h-11 items-center gap-2">
          <button type="button" className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-xl font-light text-zinc-700">＋</button>
          <input
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            className="h-10 min-w-0 flex-1 rounded-full bg-zinc-100 px-3 text-[13px] font-medium text-zinc-800 outline-none placeholder:text-zinc-400"
            placeholder="说说你想送给谁、预算多少"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming || !inputValue.trim()}
            className="h-10 rounded-full bg-[#e93b3d] px-4 text-[13px] font-black text-white shadow-[0_8px_16px_rgba(233,59,61,0.18)] disabled:bg-zinc-300 disabled:shadow-none"
          >
            {isStreaming ? '生成中' : '发送'}
          </button>
        </div>
      </form>
    </div>
  );
}

function ComboPreviewProduct({ product }: { product: (typeof comboProducts)[number] | ProductCardData }) {
  const icon = 'icon' in product ? product.icon : '🎁';
  const tone = 'tone' in product ? product.tone : 'from-sky-50 via-violet-50 to-red-50';
  const price = 'price' in product ? formatProductPrice(product.price) : '';

  return (
    <div className="rounded-2xl bg-zinc-50 p-2">
      <div className={`grid h-12 place-items-center rounded-xl bg-gradient-to-br ${tone}`}>
        <span className="text-2xl">{icon}</span>
      </div>
      <h4 className="mt-1.5 truncate text-[11px] font-black text-zinc-900">{product.name}</h4>
      <div className="mt-0.5 text-[13px] font-black text-[#e93b3d]">{price}</div>
    </div>
  );
}

export function ComboChatPage() {
  const navigate = useNavigate();
  const defaultMessage = '给老丈人送礼，预算3000元左右，想体面一点。';
  const [inputValue, setInputValue] = useState('');
  const [plan, setPlan] = useState<GiftPlanResponse | null>(() => loadGiftPlan());
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleGenerate(message = inputValue.trim() || defaultMessage) {
    if (isGenerating) return;
    setIsGenerating(true);
    setErrorMessage(null);
    try {
      const nextPlan = await generateGiftPlan({ message });
      saveGiftPlan(nextPlan);
      setPlan(nextPlan);
      setInputValue('');
    } catch (error) {
      console.error(error);
      setErrorMessage('组合礼单生成失败，请确认后端 gift-plan 接口已启动。');
    } finally {
      setIsGenerating(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void handleGenerate();
  }

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
              <p className="mt-1 text-[12px] font-bold leading-5 text-zinc-600">
                {plan?.requirement ?? '长辈关系｜预算3000｜正式送礼｜适合组合方案'}
              </p>
            </div>
          </div>
        </section>

        <section className="mt-3 space-y-3">
          <AiBubble>你好，我是京礼。复杂送礼场景我可以帮你生成组合方案。</AiBubble>
          <UserBubble>{plan?.requirement ?? defaultMessage}</UserBubble>
          <AiBubble>
            {plan?.answer ?? '这个场景不建议只推荐单个商品。给长辈或老丈人送礼，更适合组合礼单，可以同时兼顾体面感、健康关怀、家庭共享和实用价值。'}
          </AiBubble>
          {errorMessage && <div className="rounded-2xl bg-red-50 px-3 py-2 text-[12px] font-bold text-[#e93b3d]">{errorMessage}</div>}
        </section>

        <section className="mt-3 overflow-hidden rounded-[24px] bg-white p-3 shadow-sm ring-1 ring-zinc-100">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-[18px] font-black text-zinc-950">{plan?.title ?? '老丈人见面礼组合'}</h2>
              <p className="mt-0.5 text-[12px] font-bold text-zinc-500">
                预算 <span className="text-[#e93b3d]">{formatAmount(plan?.budget ?? 3000)}</span>｜
                当前组合 <span className="text-[#e93b3d]">{formatAmount(plan?.total_amount ?? 2986)}</span>｜
                剩余 {formatAmount(plan?.remaining_amount ?? 14)}
              </p>
            </div>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-700">AI 组合推荐</span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {(plan?.products.length ? plan.products : comboProducts).map((product) => (
              <ComboPreviewProduct key={product.name} product={product} />
            ))}
          </div>
          <div className="mt-3 grid gap-1.5">
            {(plan?.value_points.map((point) => `${point.title}：${point.desc}`) ?? ['体面感：正式拜访不显随意', '健康关怀：更适合长辈关系', '家庭共享：让礼物更自然']).map((item) => (
              <div key={item} className="rounded-full bg-red-50 px-3 py-1.5 text-[11px] font-black text-[#e93b3d]">
                {item}
              </div>
            ))}
          </div>
          <button
            onClick={() => navigate('/combo-plan')}
            className="mt-3 h-10 w-full rounded-full bg-gradient-to-r from-[#e93b3d] to-violet-500 text-[13px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.2)]"
          >
            {plan ? '查看完整组合礼单' : '查看静态示例礼单'}
          </button>
          {!plan && (
            <button
              onClick={() => void handleGenerate(defaultMessage)}
              disabled={isGenerating}
              className="mt-2 h-9 w-full rounded-full border border-violet-200 bg-violet-50 text-[12px] font-black text-violet-700 disabled:opacity-50"
            >
              {isGenerating ? '正在生成' : '让 AI 生成真实组合'}
            </button>
          )}
        </section>
      </div>

      <form onSubmit={handleSubmit} className="h-[76px] flex-none border-t border-zinc-200 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.05)]">
        <div className="flex h-11 items-center gap-2">
          <button type="button" className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-xl font-light text-zinc-700">＋</button>
          <input
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            className="h-10 min-w-0 flex-1 rounded-full bg-zinc-100 px-3 text-[13px] font-medium text-zinc-800 outline-none placeholder:text-zinc-400"
            placeholder="继续补充他的喜好或忌口"
            disabled={isGenerating}
          />
          <button
            type="submit"
            disabled={isGenerating}
            className="h-10 rounded-full bg-[#e93b3d] px-4 text-[13px] font-black text-white shadow-[0_8px_16px_rgba(233,59,61,0.18)] disabled:bg-zinc-300 disabled:shadow-none"
          >
            {isGenerating ? '生成中' : '发送'}
          </button>
        </div>
      </form>
    </div>
  );
}

function ComboProductRow({ product }: { product: (typeof comboProducts)[number] | ProductCardData }) {
  const icon = 'icon' in product ? product.icon : '🎁';
  const tone = 'tone' in product ? product.tone : 'from-sky-50 via-violet-50 to-red-50';
  const tags = product.tags ?? [];
  const reason = 'reason' in product ? product.reason : '';

  return (
    <article className="flex gap-3 border-b border-zinc-100 py-3 last:border-b-0">
      <div className={`grid h-[68px] w-[68px] flex-none place-items-center rounded-2xl bg-gradient-to-br ${tone} shadow-sm`}>
        <span className="text-3xl">{icon}</span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-[14px] font-black leading-5 text-zinc-950">{product.name}</h3>
          <span className="flex-none text-[16px] font-black text-[#e93b3d]">{formatProductPrice(product.price)}</span>
        </div>
        <div className="mt-1 flex flex-wrap gap-1">
          {tags.slice(0, 4).map((tag) => (
            <span key={tag} className="rounded-full bg-red-50 px-2 py-0.5 text-[9px] font-black text-[#e93b3d]">
              {tag}
            </span>
          ))}
        </div>
        <p className="mt-1 text-[11px] font-medium leading-4 text-zinc-500">{reason}</p>
      </div>
    </article>
  );
}

export function GiftComboPlanPage() {
  const navigate = useNavigate();
  const [plan, setPlan] = useState<GiftPlanResponse | null>(() => loadGiftPlan());
  const [isGenerating, setIsGenerating] = useState(false);
  const [isAddingAll, setIsAddingAll] = useState(false);

  async function handleRegenerate(preference?: string) {
    const baseMessage = plan?.requirement ?? '给老丈人送礼，预算3000元左右，想体面一点。';
    setIsGenerating(true);
    try {
      const nextPlan = await generateGiftPlan({
        message: baseMessage,
        budget: plan?.budget,
        preference,
      });
      saveGiftPlan(nextPlan);
      setPlan(nextPlan);
      if (preference === '更高端') navigate('/combo-premium');
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleAddAll() {
    const products = plan?.products ?? comboProducts.map((item, index) => ({
      product_id: `STATIC-COMBO-${index}`,
      name: item.name,
      price: item.price.replace('¥', ''),
      tags: item.tags,
      highlights: [item.reason],
      reason: item.reason,
      image_url: null,
      detail_url: null,
    }));
    setIsAddingAll(true);
    try {
      await Promise.all(products.map((product) => addGiftListItem(product)));
      navigate('/cart');
    } finally {
      setIsAddingAll(false);
    }
  }

  const shownProducts = plan?.products.length ? plan.products : comboProducts;
  const shownValuePoints = plan?.value_points ?? valuePoints;
  const shownChips = plan?.replacement_chips ?? comboChips;
  const budget = plan?.budget ?? 3000;
  const total = plan?.total_amount ?? 2986;
  const remaining = plan?.remaining_amount ?? 14;
  const usage = plan?.usage_percent ?? 99.5;

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
              <p className="text-[11px] font-bold text-zinc-500">{plan?.requirement ?? '给老丈人送礼，预算 3000 元左右，想体面一点'}</p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {[
              ['送礼对象', '老丈人'],
              ['预算范围', `${formatAmount(budget)} 左右`],
              ['送礼目标', '体面、稳妥、有心意'],
              ['关系阶段', '正式拜访 / 建立好印象'],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-zinc-50 px-2.5 py-2">
                <div className="text-[10px] font-black text-zinc-400">{label}</div>
                <div className={`mt-0.5 text-[12px] font-black ${value.includes('¥') ? 'text-[#e93b3d]' : 'text-zinc-800'}`}>{value}</div>
              </div>
            ))}
          </div>
          <div className="mt-2 rounded-2xl bg-red-50 px-3 py-2 text-[12px] font-black text-[#e93b3d]">{plan?.strategy ?? '推荐策略：组合礼单，而不是单一商品'}</div>
        </section>

        <section className="relative mt-3 overflow-hidden rounded-[22px] bg-gradient-to-br from-sky-50 via-violet-50 to-white p-3 shadow-sm ring-1 ring-white">
          <div className="absolute right-5 top-4 h-20 w-20 rounded-full bg-violet-200/40 blur-2xl" />
          <div className="relative flex items-start gap-2">
            <span className="grid h-9 w-9 flex-none place-items-center rounded-2xl bg-gradient-to-br from-sky-300 to-violet-400 text-xl shadow-[0_8px_18px_rgba(124,58,237,0.2)]">✨</span>
            <div>
              <h2 className="text-[16px] font-black text-zinc-950">为什么推荐组合礼单？</h2>
              <p className="mt-1 text-[12px] font-medium leading-5 text-zinc-600">
                {plan?.answer ?? '给长辈或老丈人送礼，单件商品容易显得单薄。组合礼单可以同时覆盖体面感、健康关怀、家庭共享和实用价值，更适合正式送礼场景。'}
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
              <h2 className="text-[18px] font-black text-zinc-950">{plan?.title ?? '老丈人见面礼组合'}</h2>
              <p className="mt-0.5 text-[12px] font-bold text-zinc-500">预算 <span className="text-[#e93b3d]">{formatAmount(budget)}</span>｜当前组合 <span className="text-[#e93b3d]">{formatAmount(total)}</span>｜剩余 {formatAmount(remaining)}</p>
            </div>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-700">AI 组合推荐</span>
          </div>
          <div className="mt-3 rounded-2xl bg-zinc-50 p-3">
            <div className="flex items-center justify-between text-[11px] font-black text-zinc-500">
              <span>总预算 {formatAmount(budget)}</span>
              <span className="text-[#e93b3d]">{usage}%</span>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-white">
              <div className="h-full rounded-full bg-gradient-to-r from-[#e93b3d] via-red-500 to-violet-500" style={{ width: `${Math.min(100, usage)}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-[10px] font-bold text-zinc-500">
              <span>已使用 {formatAmount(total)}</span>
              <span>剩余 {formatAmount(remaining)}</span>
            </div>
          </div>
        </section>

        <section className="mt-3 rounded-[22px] bg-white px-3 shadow-sm ring-1 ring-zinc-100">
          {shownProducts.map((product) => (
            <ComboProductRow key={product.name} product={product} />
          ))}
        </section>

        <section className="mt-3">
          <h2 className="text-[16px] font-black text-zinc-950">为什么这样搭配？</h2>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {shownValuePoints.map((point) => (
              <article key={point.title} className={`rounded-2xl p-2 ${'tone' in point ? point.tone : 'bg-violet-50 text-violet-700'}`}>
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
            {shownChips.map((chip) => (
              <button
                key={chip}
                onClick={() => void handleRegenerate(chip)}
                disabled={isGenerating}
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
          <button onClick={() => void handleRegenerate()} disabled={isGenerating} className="flex-1 rounded-full border border-[#e93b3d] bg-white text-[13px] font-black text-[#e93b3d] disabled:opacity-60">{isGenerating ? '生成中' : '换一套组合'}</button>
          <button onClick={() => void handleAddAll()} disabled={isAddingAll} className="flex-[1.35] rounded-full bg-[#e93b3d] text-[13px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.2)] disabled:bg-zinc-300">{isAddingAll ? '加入中' : '一键加入礼单'}</button>
        </div>
      </div>
    </div>
  );
}

export function PremiumComboPlanPage() {
  const navigate = useNavigate();
  const [plan, setPlan] = useState<GiftPlanResponse | null>(() => loadGiftPlan());
  const [isAddingAll, setIsAddingAll] = useState(false);

  async function handleAddAll() {
    const products = plan?.products ?? premiumProducts.map((item, index) => ({
      product_id: `STATIC-PREMIUM-${index}`,
      name: item.name,
      price: item.price.replace('¥', ''),
      tags: item.tags,
      highlights: [item.reason],
      reason: item.reason,
      image_url: null,
      detail_url: null,
    }));
    setIsAddingAll(true);
    try {
      await Promise.all(products.map((product) => addGiftListItem(product)));
      navigate('/cart');
    } finally {
      setIsAddingAll(false);
    }
  }

  async function handleRegenerate(preference: string) {
    const baseMessage = plan?.requirement ?? '给老丈人送礼，预算3000元左右，想体面一点。';
    const nextPlan = await generateGiftPlan({
      message: baseMessage,
      budget: plan?.budget,
      preference,
    });
    saveGiftPlan(nextPlan);
    setPlan(nextPlan);
  }

  const shownProducts = plan?.products.length ? plan.products : premiumProducts;
  const shownValuePoints = plan?.value_points ?? premiumValuePoints;
  const shownChips = plan?.replacement_chips ?? premiumChips;
  const budget = plan?.budget ?? 5000;
  const total = plan?.total_amount ?? 4968;
  const remaining = plan?.remaining_amount ?? 32;
  const usage = plan?.usage_percent ?? 99.4;

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
          ✨ {plan?.strategy ?? '已根据“更高端”偏好重新生成方案'}
        </div>

        <section className="rounded-[22px] bg-white p-3 shadow-sm ring-1 ring-zinc-100">
          <div className="flex items-center gap-2">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-amber-50 text-2xl">🎁</span>
            <div>
              <h2 className="text-[17px] font-black text-zinc-950">升级需求</h2>
              <p className="text-[11px] font-bold text-zinc-500">{plan?.requirement ?? '老丈人见面礼，从体面升级到更有分量'}</p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {[
              ['送礼对象', '老丈人'],
              ['原预算', `${formatAmount(budget)} 左右`],
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
                {plan?.answer ?? '正式拜访长辈时，礼物不只要实用，也要体现诚意和分寸。高端版方案会提升主礼品质，同时保留健康关怀和家庭共享属性。'}
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
              <h2 className="text-[18px] font-black text-zinc-950">{plan?.title ?? '老丈人见面礼组合 · 高端版'}</h2>
              <p className="mt-0.5 text-[12px] font-bold text-zinc-500">预算 <span className="text-[#e93b3d]">{formatAmount(budget)}</span>｜当前组合 <span className="text-[#e93b3d]">{formatAmount(total)}</span>｜剩余 {formatAmount(remaining)}</p>
            </div>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-black text-violet-700">AI 高端推荐</span>
          </div>
          <div className="mt-3 rounded-2xl bg-zinc-50 p-3">
            <div className="flex items-center justify-between text-[11px] font-black text-zinc-500">
              <span>总预算 {formatAmount(budget)}</span>
              <span className="text-[#e93b3d]">{usage}%</span>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-white">
              <div className="h-full rounded-full bg-gradient-to-r from-[#e93b3d] via-amber-500 to-violet-500" style={{ width: `${Math.min(100, usage)}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-[10px] font-bold text-zinc-500">
              <span>已使用 {formatAmount(total)}</span>
              <span>剩余 {formatAmount(remaining)}</span>
            </div>
          </div>
        </section>

        <section className="mt-3 rounded-[22px] bg-white px-3 shadow-sm ring-1 ring-zinc-100">
          {shownProducts.map((product) => (
            <ComboProductRow key={product.name} product={product} />
          ))}
          <div className="border-t border-zinc-100 py-3 text-right text-[15px] font-black text-[#e93b3d]">合计 {formatAmount(total)}</div>
        </section>

        <section className="mt-3">
          <h2 className="text-[16px] font-black text-zinc-950">为什么这样搭配？</h2>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {shownValuePoints.map((point) => (
              <article key={point.title} className={`rounded-2xl p-2 ${'tone' in point ? point.tone : 'bg-violet-50 text-violet-700'}`}>
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
            {shownChips.map((chip) => (
              <button key={chip} onClick={() => void handleRegenerate(chip)} className="rounded-full bg-white px-3 py-2 text-[12px] font-black text-zinc-700 shadow-sm ring-1 ring-zinc-100">{chip}</button>
            ))}
          </div>
        </section>
      </div>

      <div className="h-[76px] flex-none border-t border-zinc-200 bg-white px-3 pt-2 shadow-[0_-8px_20px_rgba(0,0,0,0.05)]">
        <div className="flex h-11 gap-2">
          <button onClick={() => navigate('/combo-plan')} className="flex-1 rounded-full border border-[#e93b3d] bg-white text-[13px] font-black text-[#e93b3d]">返回原方案</button>
          <button onClick={() => void handleAddAll()} disabled={isAddingAll} className="flex-[1.35] rounded-full bg-[#e93b3d] text-[13px] font-black text-white shadow-[0_8px_18px_rgba(233,59,61,0.2)] disabled:bg-zinc-300">{isAddingAll ? '加入中' : '一键加入礼单'}</button>
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

function CartProductRow({
  product,
  quantity,
  checked,
  onToggle,
  onDecrease,
  onIncrease,
}: {
  product: ProductCardData;
  quantity: number;
  checked: boolean;
  onToggle: (productId: string) => void;
  onDecrease: (productId: string) => void;
  onIncrease: (productId: string) => void;
}) {
  return (
    <article className="flex gap-2 border-b border-zinc-100 py-3 last:border-b-0">
      <button
        type="button"
        onClick={() => onToggle(product.product_id)}
        className={`mt-6 h-4 w-4 flex-none rounded-full border text-center text-[10px] leading-[14px] ${
          checked ? 'border-[#e93b3d] bg-[#e93b3d] text-white' : 'border-zinc-300 bg-white text-transparent'
        }`}
      >
        ✓
      </button>
      <div className="grid h-[72px] w-[72px] flex-none place-items-center rounded-2xl bg-gradient-to-br from-sky-50 via-violet-50 to-red-50">
        <span className="text-3xl">🎁</span>
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="truncate text-[13px] font-black text-zinc-950">{product.name}</h3>
        <p className="mt-0.5 truncate text-[10px] font-bold text-zinc-500">{product.reason}</p>
        <div className="mt-1 flex flex-wrap gap-1">
          {product.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="rounded bg-red-50 px-1.5 py-0.5 text-[9px] font-black text-[#e93b3d]">{tag}</span>
          ))}
        </div>
        <div className="mt-1.5 flex items-end justify-between">
          <span className="text-[16px] font-black text-[#e93b3d]">{formatProductPrice(product.price)}</span>
          <div className="flex h-6 items-center overflow-hidden rounded-full border border-zinc-200 text-[11px] font-black">
            <button type="button" onClick={() => onDecrease(product.product_id)} className="px-2 text-zinc-400">-</button>
            <span className="bg-zinc-50 px-2 text-zinc-800">{quantity}</span>
            <button type="button" onClick={() => onIncrease(product.product_id)} className="px-2 text-zinc-700">+</button>
          </div>
        </div>
      </div>
    </article>
  );
}

export function GiftCartPage() {
  const navigate = useNavigate();
  const [giftList, setGiftList] = useState<GiftListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set());
  const [localQuantities, setLocalQuantities] = useState<Record<string, number>>({});
  const [checkoutPreview, setCheckoutPreview] = useState<GiftListCheckoutPreviewResponse | null>(null);
  const [isPreviewingCheckout, setIsPreviewingCheckout] = useState(false);
  const [checkoutErrorMessage, setCheckoutErrorMessage] = useState<string | null>(null);

  function syncCartState(nextList: GiftListResponse) {
    setGiftList(nextList);
    setLocalQuantities(
      Object.fromEntries(nextList.items.map((item) => [item.product.product_id, item.quantity])),
    );
    setSelectedIds((current) => {
      const availableIds = new Set(nextList.items.map((item) => item.product.product_id));
      const next = new Set([...current].filter((productId) => availableIds.has(productId)));
      if (current.size === 0) {
        nextList.items.forEach((item) => next.add(item.product.product_id));
      }
      return next;
    });
  }

  useEffect(() => {
    void getGiftList()
      .then((nextList) => {
        syncCartState(nextList);
        setSelectedIds(new Set(nextList.items.map((item) => item.product.product_id)));
      })
      .finally(() => setIsLoading(false));
  }, []);

  async function handleRemove(productId: string) {
    const nextList = await removeGiftListItem(productId);
    syncCartState(nextList);
    setSelectedIds((current) => {
      const next = new Set(current);
      next.delete(productId);
      return next;
    });
    setLocalQuantities((current) => {
      const next = { ...current };
      delete next[productId];
      return next;
    });
  }

  function handleToggle(productId: string) {
    setCheckoutPreview(null);
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(productId)) {
        next.delete(productId);
      } else {
        next.add(productId);
      }
      return next;
    });
  }

  function handleToggleAll() {
    setCheckoutPreview(null);
    setSelectedIds((current) => {
      if (current.size === items.length) return new Set();
      return new Set(items.map((item) => item.product.product_id));
    });
  }

  function handleIncrease(productId: string) {
    setCheckoutPreview(null);
    const nextQuantity = Math.min(99, (localQuantities[productId] ?? 1) + 1);
    setLocalQuantities((current) => ({ ...current, [productId]: nextQuantity }));
    setSelectedIds((current) => new Set(current).add(productId));
    void updateGiftListItemQuantity(productId, nextQuantity).then(syncCartState);
  }

  function handleDecrease(productId: string) {
    setCheckoutPreview(null);
    const currentQuantity = localQuantities[productId] ?? 1;
    if (currentQuantity <= 1) {
      void handleRemove(productId);
      return;
    }
    const nextQuantity = currentQuantity - 1;
    setLocalQuantities((current) => ({ ...current, [productId]: nextQuantity }));
    void updateGiftListItemQuantity(productId, nextQuantity).then(syncCartState);
  }

  async function handlePreviewCheckout() {
    if (selectedItems.length === 0 || isPreviewingCheckout) return;
    setIsPreviewingCheckout(true);
    setCheckoutErrorMessage(null);
    try {
      const preview = await previewGiftListCheckout(
        selectedItems.map((item) => ({
          product_id: item.product.product_id,
          quantity: localQuantities[item.product.product_id] ?? item.quantity,
        })),
      );
      setCheckoutPreview(preview);
    } catch (error) {
      console.error(error);
      setCheckoutErrorMessage('结算预览失败，请确认后端礼单接口已启动。');
    } finally {
      setIsPreviewingCheckout(false);
    }
  }

  const items = giftList?.items ?? [];
  const totalCount = items.reduce((sum, item) => sum + (localQuantities[item.product.product_id] ?? item.quantity), 0);
  const allChecked = items.length > 0 && selectedIds.size === items.length;
  const selectedItems = items.filter((item) => selectedIds.has(item.product.product_id));
  const selectedCount = selectedItems.reduce((sum, item) => sum + (localQuantities[item.product.product_id] ?? item.quantity), 0);
  const selectedAmount = selectedItems.reduce(
    (sum, item) => sum + toAmount(item.product.price) * (localQuantities[item.product.product_id] ?? item.quantity),
    0,
  );

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#f3f4f7]">
      <StatusBar />
      <header className="flex h-[52px] flex-none items-center bg-white px-3">
        <button onClick={() => navigate('/combo-plan')} className="grid h-9 w-9 place-items-center rounded-full bg-zinc-100 text-2xl font-light text-zinc-800">‹</button>
        <h1 className="flex-1 text-center text-[18px] font-black text-zinc-950">购物车（{totalCount}）</h1>
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
          ✨ 京礼已为你加入 {totalCount} 件商品，组成 AI 智能礼单
        </div>
        {checkoutErrorMessage && (
          <div className="mt-2 rounded-2xl bg-red-50 px-3 py-2 text-[12px] font-black text-[#e93b3d]">
            {checkoutErrorMessage}
          </div>
        )}

        <section className="mt-2 rounded-[22px] bg-white px-3 shadow-sm">
          <div className="flex items-center border-b border-zinc-100 py-3">
            <span className="mr-2 h-4 w-4 rounded-full bg-[#e93b3d] text-center text-[10px] leading-4 text-white">✓</span>
            <h2 className="flex-1 text-[14px] font-black text-zinc-950">京礼精选组合</h2>
            <span className="text-zinc-400">›</span>
          </div>
          {isLoading && <div className="py-6 text-center text-[12px] font-bold text-zinc-400">正在读取礼单...</div>}
          {!isLoading && items.length === 0 && (
            <div className="py-8 text-center">
              <div className="text-3xl">🎁</div>
              <p className="mt-2 text-[13px] font-black text-zinc-800">礼单还是空的</p>
              <button
                onClick={() => navigate('/jingli')}
                className="mt-3 rounded-full bg-[#e93b3d] px-4 py-2 text-[12px] font-black text-white"
              >
                去问京礼
              </button>
            </div>
          )}
          {items.map((item) => (
            <CartProductRow
              key={item.product.product_id}
              product={item.product}
              quantity={localQuantities[item.product.product_id] ?? item.quantity}
              checked={selectedIds.has(item.product.product_id)}
              onToggle={handleToggle}
              onDecrease={handleDecrease}
              onIncrease={handleIncrease}
            />
          ))}
        </section>

        {checkoutPreview && (
          <section className="mt-2 rounded-[22px] bg-white p-3 shadow-sm ring-1 ring-emerald-50">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="text-[15px] font-black text-zinc-950">结算确认</h2>
                <p className="mt-1 text-[11px] font-bold text-zinc-500">
                  已选择 {checkoutPreview.total_count} 件商品，后端已重新确认金额
                </p>
              </div>
              <span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-black text-emerald-600">
                可提交
              </span>
            </div>
            <div className="mt-2 space-y-1.5">
              {checkoutPreview.items.map((item) => (
                <div key={item.product.product_id} className="flex items-center justify-between rounded-xl bg-zinc-50 px-2 py-1.5">
                  <span className="min-w-0 flex-1 truncate text-[11px] font-black text-zinc-800">
                    {item.product.name} x {item.quantity}
                  </span>
                  <span className="text-[12px] font-black text-[#e93b3d]">{formatAmount(item.subtotal)}</span>
                </div>
              ))}
            </div>
            {!!checkoutPreview.unavailable_product_ids.length && (
              <div className="mt-2 rounded-xl bg-amber-50 px-2 py-1.5 text-[10px] font-black text-amber-700">
                有 {checkoutPreview.unavailable_product_ids.length} 件商品暂不可结算
              </div>
            )}
            <div className="mt-3 flex items-center justify-between border-t border-zinc-100 pt-2">
              <span className="text-[12px] font-bold text-zinc-500">确认合计</span>
              <span className="text-[20px] font-black text-[#e93b3d]">{formatAmount(checkoutPreview.total_amount)}</span>
            </div>
          </section>
        )}

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
          <button type="button" onClick={handleToggleAll} className="flex items-center gap-1 text-[12px] font-black text-zinc-700">
            <span
              className={`h-4 w-4 rounded-full border text-center text-[10px] leading-[14px] ${
                allChecked ? 'border-[#e93b3d] bg-[#e93b3d] text-white' : 'border-zinc-300 bg-white text-transparent'
              }`}
            >
              ✓
            </span>
            全选
          </button>
          <div className="min-w-0 flex-1 text-right">
            <div className="text-[12px] font-bold text-zinc-600">合计：<span className="text-[18px] font-black text-[#e93b3d]">{formatAmount(selectedAmount)}</span></div>
            <div className="text-[10px] font-bold text-zinc-400">已选 {selectedCount} 件｜礼单共 {totalCount} 件</div>
          </div>
          <button
            disabled={selectedCount === 0}
            onClick={() => void handlePreviewCheckout()}
            className="h-10 rounded-full bg-[#e93b3d] px-4 text-[13px] font-black text-white shadow-[0_8px_16px_rgba(233,59,61,0.2)] disabled:bg-zinc-300 disabled:shadow-none"
          >
            {isPreviewingCheckout ? '确认中' : `去结算（${selectedCount}）`}
          </button>
        </div>
      </div>
      <CartTabBar />
    </div>
  );
}

export function LegacyHomePage() {
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

export function HomePage() {
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
