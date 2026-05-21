/**
 * v2 推荐方案视图：渲染 RAG 召回 + LLM 重排后返回的真实商品 + 价值点 + 总结文案
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Icon } from '../components/Icon';
import { useV2 } from '../state/V2Context';
import type { V2Recommendation } from '../api/v2Api';
import { addV2CartItem, removeV2CartItem } from '../api/v2CartApi';
import type { ProductCardData } from '../../api/chat';

const recToProductCard = (rec: V2Recommendation): ProductCardData => ({
  product_id: rec.productId,
  name: rec.name,
  image_url: rec.imageUrl,
  price: rec.price,
  tags: rec.tags,
  highlights: [rec.rationale],
  reason: rec.rationale,
  display_reason: rec.rationale,
  scenarios: rec.scenarios,
  target_people: rec.targetPeople,
});

function ProductImage({ rec }: { rec: V2Recommendation }) {
  if (!rec.imageUrl) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-center text-slate-400">
        <Icon name="image" className="mb-3 h-8 w-8 text-slate-400" />
        <button
          type="button"
          className="rounded-md bg-[#f59e0b] px-3 py-1.5 text-[10px] font-black text-white shadow-sm"
        >
          生成实物图
        </button>
      </div>
    );
  }
  return (
    <img
      src={rec.imageUrl}
      alt={rec.name}
      className="h-full w-full rounded-2xl object-cover"
      onError={(e) => {
        const target = e.currentTarget as HTMLImageElement;
        target.style.display = 'none';
        const fallback = target.parentElement?.querySelector('[data-fallback]');
        if (fallback) (fallback as HTMLElement).style.display = 'flex';
      }}
    />
  );
}

interface SolutionCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  accent: string;
}

function SolutionCard({ label, value, icon, accent }: SolutionCardProps) {
  return (
    <div className="flex items-start gap-3 rounded-2xl bg-slate-50 p-3.5">
      <div
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
        style={{ backgroundColor: accent + '12' }}
      >
        <div style={{ color: accent }}>{icon}</div>
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-black text-slate-700">{label}</div>
        <div className="mt-1 text-[11px] font-semibold leading-relaxed text-slate-500">{value}</div>
      </div>
    </div>
  );
}

export default function V2RecommendationsPage() {
  const navigate = useNavigate();
  const { recommendations, showToast, setCartItems, triggerIsland } = useV2();
  const [addedIds, setAddedIds] = useState<Set<string>>(() => new Set());
  const [isAddingAll, setIsAddingAll] = useState(false);

  // 直接刷新此页面没有数据时，引导用户回到 wizard
  useEffect(() => {
    if (!recommendations) {
      const timer = window.setTimeout(() => navigate('/v2/wizard', { replace: true }), 50);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [recommendations, navigate]);

  if (!recommendations) {
    return (
      <div className="flex h-full items-center justify-center text-[12px] text-slate-500">
        正在跳转到画像配置...
      </div>
    );
  }

  async function handlePickToCart(rec: V2Recommendation) {
    try {
      const isAdded = addedIds.has(rec.productId);
      const next = isAdded
        ? await removeV2CartItem(rec.productId)
        : await addV2CartItem(recToProductCard(rec));
      setCartItems(next);
      setAddedIds((prev) => {
        const nextIds = new Set(prev);
        if (isAdded) {
          nextIds.delete(rec.productId);
        } else {
          nextIds.add(rec.productId);
        }
        return nextIds;
      });
      triggerIsland(isAdded ? '已移出购物车' : '已加入礼单', `${rec.name} · 京礼礼单`, 3000);
    } catch (err) {
      console.error(err);
      showToast('更新购物车失败，请确认后端礼单服务已启动');
    }
  }

  async function handleAddAllToCart() {
    if (isAddingAll || !recommendations) return;
    const allAdded = recommendations.recommendations.every((gift) => addedIds.has(gift.productId));
    const targets = allAdded
      ? recommendations.recommendations
      : recommendations.recommendations.filter((gift) => !addedIds.has(gift.productId));
    setIsAddingAll(true);
    try {
      let nextItems = null;
      for (const gift of targets) {
        nextItems = allAdded
          ? await removeV2CartItem(gift.productId)
          : await addV2CartItem(recToProductCard(gift));
      }
      if (nextItems) setCartItems(nextItems);
      setAddedIds((prev) => {
        const next = new Set(prev);
        targets.forEach((gift) => {
          if (allAdded) {
            next.delete(gift.productId);
          } else {
            next.add(gift.productId);
          }
        });
        return next;
      });
      triggerIsland(
        allAdded ? '已移出整套方案' : '已加入整套方案',
        `${targets.length} 件礼物已${allAdded ? '移出' : '加入'}购物车`,
        3000,
      );
    } catch (err) {
      console.error(err);
      showToast('更新整套方案失败，请确认后端礼单服务已启动');
    } finally {
      setIsAddingAll(false);
    }
  }

  const { answer, recommendations: list, shapeDecision, solution } = recommendations;
  const isCombo = shapeDecision?.shape === 'gift_combo';
  const introCount = Math.max(list.length, 1);
  const introTitle = isCombo ? 'AI 已定制如下组合礼包' : 'AI 已精选如下单品礼物';
  const introSubtitle = isCombo
    ? '为您生成 1 套主礼与副礼搭配方案，并补齐送礼话术与行动建议。'
    : `为您在商品库中筛选了 ${introCount} 个更适合单独赠送的候选礼物。`;

  return (
    <div className="min-h-full bg-[#f8f9fb] px-5 pb-7 pt-4 text-slate-950 animate-fadeIn">
      <div className="mb-5 flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate('/v2/wizard')}
          className="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-white hover:text-slate-900"
        >
          <Icon name="chevron-left" className="h-[18px] w-[18px]" />
        </button>
        <span className="text-[13px] font-black text-slate-400">AI 推荐礼品清单</span>
        <div className="w-8" />
      </div>

      <section className="mb-5 rounded-[18px] border border-[#ffe4a8] bg-gradient-to-br from-[#fffdf4] via-[#fff8f1] to-[#fff3f7] px-4 py-4 shadow-sm">
        <div className="flex items-start gap-2">
          <Icon name="sparkles" className="mt-0.5 h-5 w-5 shrink-0 text-[#f59e0b]" />
          <div>
            <h1 className="text-[15px] font-black tracking-tight text-slate-950">
              {introTitle}
            </h1>
            <p className="mt-1 text-[11px] font-semibold leading-5 text-slate-500">
              {introSubtitle}
            </p>
          </div>
        </div>
      </section>

      {/* ===== 商品列表（前置） ===== */}
      <div className="space-y-4">
        {list.map((gift, idx) => {
          const isAdded = addedIds.has(gift.productId);
          return (
            <article
              key={gift.productId}
              className="grid grid-cols-[108px_minmax(0,1fr)] gap-4 rounded-[18px] bg-white p-4 shadow-[0_8px_20px_rgba(15,23,42,0.06)] ring-1 ring-slate-100"
            >
              <div className="min-w-0">
                <div className="h-[108px] w-[108px] overflow-hidden rounded-2xl bg-slate-50">
                  <ProductImage rec={gift} />
                </div>
                <p className="mt-2 truncate text-center text-[10px] font-black text-slate-400">
                  {gift.tags[0] || gift.scenarios[0] || `方案 ${idx + 1}`}
                </p>
              </div>

              <div className="min-w-0">
                <div className="mb-1.5 flex items-start justify-between gap-3">
                  <h2 className="min-w-0 flex-1 text-[14px] font-black leading-5 text-slate-950 line-clamp-2">
                    {isCombo && gift.giftRole === 'main_gift' ? '主礼 · ' : ''}
                    {isCombo && gift.giftRole === 'addon_gift' ? '副礼 · ' : ''}
                    {!isCombo && idx === 0 ? '首推 · ' : ''}
                    {!isCombo && idx > 0 ? `备选${idx} · ` : ''}
                    {gift.name}
                  </h2>
                  <span className="shrink-0 text-[14px] font-black text-[#ff3f63]">¥{gift.price}</span>
                </div>

                <p className="mb-3 text-[11px] font-semibold leading-5 text-slate-500 line-clamp-3">
                  {gift.rationale || answer || '这份礼物匹配当前画像，适合作为专属送礼方案。'}
                </p>

                <div className="mb-3 flex flex-wrap gap-1.5">
                  {(gift.tags.length > 0 ? gift.tags : gift.scenarios).slice(0, 2).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-lg bg-[#fff0f2] px-2.5 py-1 text-[10px] font-black text-[#ff3f63]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between gap-2">
                  <button
                    type="button"
                    className="rounded-lg bg-[#fff0f2] px-3 py-2 text-[10px] font-black text-[#ff3f63]"
                  >
                    写专属语音卡
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePickToCart(gift)}
                    className={`rounded-xl px-4 py-2 text-[10px] font-black shadow-[0_8px_16px_rgba(2,7,25,0.14)] transition active:scale-95 ${
                      isAdded
                        ? 'bg-emerald-500 text-white'
                        : 'bg-[#020719] text-white'
                    }`}
                  >
                    {isAdded ? '取消加入' : '加入购物车'}
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {/* ===== 解决方案（后置 + 美化） ===== */}
      {isCombo && solution && (
        <section className="mt-5 rounded-[18px] bg-white p-4 shadow-[0_8px_20px_rgba(15,23,42,0.06)] ring-1 ring-slate-100">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#fff0f2]">
                <Icon name="gift" className="h-4 w-4 text-[#ff3f63]" />
              </div>
              <h2 className="text-[14px] font-black text-slate-950">完整送礼解决方案</h2>
            </div>
            <span className="rounded-full bg-[#fff0f2] px-2.5 py-1 text-[9px] font-black text-[#ff3f63]">
              组合方案
            </span>
          </div>

          <p className="mb-4 text-[11px] font-semibold leading-relaxed text-slate-500">
            {solution.recommendationReason || answer}
          </p>

          <div className="grid gap-2.5">
            <SolutionCard
              label="送礼话术"
              value={solution.giftTalk}
              icon={<Icon name="message-circle" className="h-4 w-4" />}
              accent="#818cf8"
            />
            <SolutionCard
              label="送礼时机"
              value={solution.givingTiming}
              icon={<Icon name="clock" className="h-4 w-4" />}
              accent="#fbbf24"
            />
            <SolutionCard
              label="送礼地点"
              value={solution.givingPlace}
              icon={<Icon name="map-pin" className="h-4 w-4" />}
              accent="#34d399"
            />
            <SolutionCard
              label="包装建议"
              value={solution.packagingAdvice}
              icon={<Icon name="box" className="h-4 w-4" />}
              accent="#a78bfa"
            />
            <SolutionCard
              label="对方推辞时"
              value={solution.recipientReactionReply}
              icon={<Icon name="heart" className="h-4 w-4" />}
              accent="#fb7185"
            />
          </div>

          {solution.avoidTips.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {solution.avoidTips.slice(0, 3).map((tip) => (
                <span
                  key={tip}
                  className="rounded-full bg-amber-50 px-3 py-1 text-[9px] font-black text-amber-700"
                >
                  避坑：{tip}
                </span>
              ))}
            </div>
          )}

          <button
            type="button"
            onClick={handleAddAllToCart}
            disabled={isAddingAll}
            className={`mt-5 h-10 w-full rounded-2xl text-[11px] font-black text-white shadow-[0_8px_16px_rgba(2,7,25,0.14)] transition active:scale-[0.98] ${
              list.every((gift) => addedIds.has(gift.productId)) ? 'bg-emerald-500' : 'bg-[#020719]'
            }`}
          >
            {list.every((gift) => addedIds.has(gift.productId))
              ? '取消加入整套方案'
              : isAddingAll
                ? '正在加入整套方案'
                : '一键加入整套方案'}
          </button>
        </section>
      )}

      {!isCombo && solution && (
        <section className="mt-5 rounded-[18px] bg-white p-4 shadow-[0_8px_20px_rgba(15,23,42,0.06)] ring-1 ring-slate-100">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#fff0f2]">
                <Icon name="gift" className="h-4 w-4 text-[#ff3f63]" />
              </div>
              <h2 className="text-[14px] font-black text-slate-950">单品送礼建议</h2>
            </div>
            <span className="rounded-full bg-[#fff0f2] px-2.5 py-1 text-[9px] font-black text-[#ff3f63]">
              选 1 件即可
            </span>
          </div>

          <p className="mb-4 text-[11px] font-semibold leading-relaxed text-slate-500">
            {solution.recommendationReason || solution.summary || answer}
          </p>

          <div className="grid gap-2.5">
            <SolutionCard
              label="怎么说"
              value={solution.giftTalk}
              icon={<Icon name="message-circle" className="h-4 w-4" />}
              accent="#818cf8"
            />
            <SolutionCard
              label="什么时候送"
              value={solution.givingTiming}
              icon={<Icon name="clock" className="h-4 w-4" />}
              accent="#fbbf24"
            />
            <SolutionCard
              label="包装建议"
              value={solution.packagingAdvice}
              icon={<Icon name="box" className="h-4 w-4" />}
              accent="#a78bfa"
            />
          </div>
        </section>
      )}

      {list.length > 0 && (
        <div className="sticky bottom-3 mt-5 rounded-[18px] bg-white/95 p-3 shadow-[0_10px_28px_rgba(15,23,42,0.12)] ring-1 ring-slate-100 backdrop-blur">
          {isCombo ? (
            <div className="grid grid-cols-[1fr_1.05fr] gap-2">
              <button
                type="button"
                onClick={handleAddAllToCart}
                disabled={isAddingAll}
                className={`h-11 rounded-2xl text-[11px] font-black text-white shadow-[0_12px_24px_rgba(2,7,25,0.14)] transition active:scale-[0.98] ${
                  list.every((gift) => addedIds.has(gift.productId)) ? 'bg-emerald-500' : 'bg-[#020719]'
                }`}
              >
                {list.every((gift) => addedIds.has(gift.productId)) ? '取消整套' : '加入整套'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/v2/cart')}
                className="h-11 rounded-2xl bg-gradient-to-r from-[#ff3f63] via-[#ff6b35] to-[#f59e0b] text-[11px] font-black text-white shadow-[0_12px_24px_rgba(255,63,99,0.18)] transition active:scale-[0.98]"
              >
                去购物车结算
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => navigate('/v2/cart')}
              className="h-11 w-full rounded-2xl bg-gradient-to-r from-[#ff3f63] via-[#ff6b35] to-[#f59e0b] text-[12px] font-black text-white shadow-[0_12px_24px_rgba(255,63,99,0.18)] transition active:scale-[0.98]"
            >
              去购物车查看并结算
            </button>
          )}
        </div>
      )}

      {list.length === 0 && (
        <div className="rounded-2xl bg-white p-5 text-center text-[12px] font-bold text-slate-500 shadow-sm ring-1 ring-slate-100">
          暂时没有匹配到合适礼品，请返回修改画像条件。
        </div>
      )}
    </div>
  );
}
