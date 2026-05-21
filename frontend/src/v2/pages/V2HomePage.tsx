/**
 * v2 首页：搜索中心 + 甄选商品，与整体浅色清爽风格统一。
 * 搜索框输入「节日」或「520」后跳转到 /v2/wizard。
 */
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Icon } from '../components/Icon';
import { getInstantProducts, type V2InstantProduct } from '../api/v2Api';
import { addV2CartItem } from '../api/v2CartApi';
import { useV2 } from '../state/V2Context';
import type { ProductCardData } from '../../api/chat';

const HOT_SEARCHES = ['520', '节日', '生日', '纪念日', '母亲节'];

const SEARCH_SUGGESTIONS: Record<string, string[]> = {
  '520': ['京礼-AI送礼助手', '520 礼物', '520 送男朋友礼物', '520 礼盒', '520 贺卡'],
  '节日': ['节日送父母礼物', '节日礼盒', '节日送领导', '节日伴手礼'],
  '生日': ['生日礼物', '生日惊喜', '生日礼盒', '生日送妈妈'],
};

const fallbackProducts: V2InstantProduct[] = [
  {
    id: 'fallback-aroma',
    name: '巴黎幽境 · 轻奢手工香氛礼盒',
    price: 299,
    image: 'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&q=80&w=600',
    desc: '温柔木质香调，适合生日和日常关怀。',
    tag: '生活美学',
  },
  {
    id: 'fallback-mic',
    name: '落日余晖 · 复古黑胶无线音箱',
    price: 458,
    image: 'https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&q=80&w=600',
    desc: '复古造型与氛围灯效，适合有品味的 TA。',
    tag: '高端数码',
  },
  {
    id: 'fallback-pen',
    name: '低调绅士 · 极简金属签字笔',
    price: 168,
    image: 'https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?auto=format&fit=crop&q=80&w=600',
    desc: '商务、教师、同事场景都稳妥。',
    tag: '文具礼品',
  },
  {
    id: 'fallback-box',
    name: '粉金礼遇 · 高定惊喜礼盒',
    price: 399,
    image: 'https://images.unsplash.com/photo-1549465220-1a8b9238cd48?auto=format&fit=crop&q=80&w=600',
    desc: '仪式感包装，适合节日和纪念日。',
    tag: '智能家居',
  },
];

const toProductCard = (prod: V2InstantProduct): ProductCardData => ({
  product_id: prod.id,
  name: prod.name,
  image_url: prod.image || null,
  price: prod.price,
  tags: [prod.tag],
  highlights: [prod.desc],
  reason: prod.desc || '适合作为京礼精选礼物',
  display_reason: prod.desc || '适合作为京礼精选礼物',
});

function ProductImage({ product }: { product: V2InstantProduct }) {
  const [failed, setFailed] = useState(false);
  if (!product.image || failed) {
    return (
      <div className="grid h-full w-full place-items-center bg-gradient-to-br from-slate-100 via-white to-orange-50 text-2xl">
        🎁
      </div>
    );
  }
  return (
    <img
      src={product.image}
      alt={product.name}
      className="h-full w-full object-cover"
      onError={() => setFailed(true)}
    />
  );
}

function HomeProductCard({
  product,
  onAdd,
}: {
  product: V2InstantProduct;
  onAdd: (product: V2InstantProduct) => void;
}) {
  return (
    <article className="overflow-hidden rounded-[18px] bg-white shadow-sm ring-1 ring-slate-100">
      <div className="relative h-[92px] overflow-hidden bg-slate-100">
        <ProductImage product={product} />
        <span className="absolute left-2.5 top-2.5 rounded-full bg-slate-950/70 px-2 py-0.5 text-[11px] font-black text-white backdrop-blur">
          {product.tag || '精选好礼'}
        </span>
      </div>
      <div className="p-2.5">
        <h3 className="line-clamp-2 min-h-8 text-[12px] font-black leading-4 text-slate-950">
          {product.name}
        </h3>
        <p className="mt-1 line-clamp-2 min-h-7 text-[12px] font-semibold leading-[13px] text-slate-500">
          {product.desc || '京礼精选，体面送礼。'}
        </p>
        <div className="mt-1 text-[16px] font-black tracking-tight text-[#e4393c]">
          ¥{Math.round(product.price).toLocaleString('zh-CN')}
        </div>
        <button
          type="button"
          onClick={() => onAdd(product)}
          className="mt-2 h-8 w-full rounded-xl bg-gradient-to-r from-[#e4393c] to-[#e4393c] text-[12px] font-black text-white shadow-md transition active:scale-[0.98]"
        >
          加入购物车
        </button>
      </div>
    </article>
  );
}

function HighlightText({ text, match }: { text: string; match: string }) {
  if (!match) return <>{text}</>;
  const parts = text.split(new RegExp(`(${match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === match.toLowerCase() ? (
          <span key={i} className="text-[#e4393c]">{part}</span>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

export default function V2HomePage() {
  const navigate = useNavigate();
  const { showToast, setCartItems, triggerIsland } = useV2();
  const [products, setProducts] = useState<V2InstantProduct[]>([]);
  const [query, setQuery] = useState('');
  const [aiSearch, setAiSearch] = useState(false);
  const displayProducts = useMemo(() => (products.length ? products : fallbackProducts), [products]);

  useEffect(() => {
    let alive = true;
    getInstantProducts(4)
      .then((items) => {
        if (alive) setProducts(items);
      })
      .catch((err) => {
        console.error(err);
        if (alive) showToast('商品库暂时不可用，已展示本地精选样例');
      });
    return () => {
      alive = false;
    };
  }, [showToast]);

  const suggestions = useMemo(() => {
    const trimmed = query.trim();
    if (!trimmed) return [];
    const key = Object.keys(SEARCH_SUGGESTIONS).find((k) => trimmed.includes(k));
    if (!key) return [];
    return SEARCH_SUGGESTIONS[key].filter(
      (s) => s === '京礼-AI送礼助手' || s.toLowerCase().includes(trimmed.toLowerCase()),
    );
  }, [query]);

  function handleSearch() {
    const trimmed = query.trim();
    if (trimmed === '节日' || trimmed === '520') {
      navigate('/v2/wizard');
    } else if (trimmed) {
      showToast(`搜索「${trimmed}」功能即将上线`);
    }
  }

  function handleSuggestionClick(suggestion: string) {
    setQuery(suggestion);
    navigate('/v2/wizard');
  }

  async function handleAdd(product: V2InstantProduct) {
    try {
      const next = await addV2CartItem(toProductCard(product));
      setCartItems(next);
      triggerIsland('已加入购物车', product.name, 3000);
    } catch (err) {
      console.error(err);
      showToast('加入购物车失败，请确认后端已启动');
    }
  }

  return (
    <div className="min-h-full bg-[#f8f9fb] px-4 pb-24 pt-4 text-slate-950 animate-fadeIn">
      {/* 搜索卡片 */}
      <div className="mb-4 rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
        <div className="flex items-center gap-2">
          <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 focus-within:border-[#e4393c]">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索礼物、场合、对象..."
              className="flex-1 bg-transparent text-[14px] font-bold text-slate-900 outline-none placeholder:font-normal placeholder:text-slate-400"
            />
            {query && (
              <button onClick={() => setQuery('')} className="text-slate-400 transition hover:text-slate-600">
                <Icon name="x" className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <label className="flex cursor-pointer items-center gap-1.5 text-[12px] font-bold text-slate-600">
              <span className="text-[#e4393c]">Ai</span> 搜索
              <input
                type="checkbox"
                checked={aiSearch}
                onChange={(e) => setAiSearch(e.target.checked)}
                className="h-4 w-4 accent-[#e4393c]"
              />
            </label>
            <button className="text-slate-400 transition hover:text-slate-600">
              <Icon name="image" className="h-5 w-5" />
            </button>
          </div>
          <button
            onClick={handleSearch}
            className="rounded-lg bg-[#e4393c] px-5 py-1.5 text-[12px] font-bold text-white shadow-sm transition active:scale-95"
          >
            搜索
          </button>
        </div>
      </div>

      {/* 搜索建议 */}
      {suggestions.length > 0 && (
        <div className="mb-4 rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
          <div className="space-y-3">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => handleSuggestionClick(s)}
                className="flex w-full items-center gap-2.5 text-left transition"
              >
                <Icon name="info" className="h-3.5 w-3.5 shrink-0 text-slate-300" />
                <span className="text-[14px] text-slate-700">
                  <HighlightText text={s} match={query.trim()} />
                </span>
              </button>
            ))}
          </div>
          <div className="mt-4 flex items-center justify-end gap-2 border-t border-slate-50 pt-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-50">
              <Icon name="sparkles" className="h-4 w-4 text-indigo-500" />
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#e4393c]">
              <Icon name="mic" className="h-4 w-4 text-white" />
            </div>
          </div>
        </div>
      )}

      {/* 热门搜索 */}
      {!query && (
        <div className="mb-5">
          <h3 className="mb-2 text-[12px] font-bold text-slate-500">热门搜索</h3>
          <div className="flex flex-wrap gap-2">
            {HOT_SEARCHES.map((tag) => (
              <button
                key={tag}
                onClick={() => {
                  setQuery(tag);
                  if (tag === '节日' || tag === '520') {
                    navigate('/v2/wizard');
                  }
                }}
                className="rounded-full bg-white px-3 py-1.5 text-[12px] font-bold text-slate-600 shadow-sm ring-1 ring-slate-100 transition hover:text-[#e4393c] hover:ring-[#e4393c]/30"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 商品展示 */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[16px] font-black text-slate-900">今日甄选</h2>
          <span className="text-[11px] font-bold tracking-wider text-slate-300">REAL STOCK</span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {displayProducts.map((product) => (
            <HomeProductCard key={product.id} product={product} onAdd={handleAdd} />
          ))}
        </div>
      </section>
    </div>
  );
}
