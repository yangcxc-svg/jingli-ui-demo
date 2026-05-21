/**
 * v2 购物车页：浅色清爽风格，与整体统一。
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Icon } from '../components/Icon';
import { useV2 } from '../state/V2Context';
import { decreaseV2CartItem, fetchV2Cart, removeV2CartItem } from '../api/v2CartApi';

const formatYuan = (n: number) => `¥${Math.round(n).toLocaleString('zh-CN')}`;

export default function V2CartPage() {
  const navigate = useNavigate();
  const { cartItems, setCartItems, clearCart, showToast } = useV2();
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setIsLoading(true);
    fetchV2Cart()
      .then((items) => {
        if (alive) setCartItems(items);
      })
      .catch(() => {
        if (alive) showToast('读取礼单失败，请确认后端已启动');
      })
      .finally(() => {
        if (alive) setIsLoading(false);
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const subtotal = cartItems.reduce((s, it) => s + it.price, 0);

  async function handleClearAll() {
    if (cartItems.length === 0) return;
    setBusyId('__all__');
    try {
      const uniqueIds = Array.from(new Set(cartItems.map((it) => it.productId)));
      let next = cartItems;
      for (const productId of uniqueIds) {
        next = await removeV2CartItem(productId);
      }
      setCartItems(next);
      clearCart();
    } catch {
      showToast('清空失败，请重试');
    } finally {
      setBusyId(null);
    }
  }

  async function handleRemoveOne(productId: string) {
    setBusyId(productId);
    try {
      const next = await decreaseV2CartItem(productId, cartItems);
      setCartItems(next);
    } catch {
      showToast('移除失败，请重试');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="min-h-full bg-[#f8f9fb] px-4 pb-24 pt-4 text-slate-950 animate-fadeIn">
      <div className="mb-5 flex items-center justify-between">
        <button
          onClick={() => navigate('/v2/home')}
          className="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-white"
          aria-label="返回首页"
        >
          <Icon name="chevron-left" className="h-5 w-5" />
        </button>
        <span className="text-[16px] font-black text-slate-900">购物车 ({cartItems.length})</span>
        <button
          onClick={handleClearAll}
          disabled={cartItems.length === 0 || busyId !== null}
          className="text-[11px] text-slate-400 transition hover:text-[#e4393c] disabled:opacity-40"
        >
          清空
        </button>
      </div>

      {isLoading ? (
        <div className="py-20 text-center text-[12px] text-slate-400">正在读取礼单...</div>
      ) : cartItems.length === 0 ? (
        <div className="py-20 text-center">
          <Icon name="shopping-bag" className="mx-auto mb-3 h-12 w-12 text-slate-200" />
          <p className="text-[14px] text-slate-400">购物车内没有任何商品</p>
          <button
            onClick={() => navigate('/v2/home')}
            className="mt-4 text-[12px] font-bold text-[#e4393c] underline"
          >
            返回首页
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {cartItems.map((item, index) => (
            <div
              key={`${item.productId}-${index}`}
              className="flex gap-4 rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100"
            >
              <div className="h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-slate-50">
                {item.imageUrl ? (
                  <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <Icon name="image" className="h-6 w-6 text-slate-300" />
                  </div>
                )}
              </div>
              <div className="flex flex-1 flex-col justify-between">
                <div>
                  <h5 className="text-[14px] font-black leading-snug text-slate-950 line-clamp-2">{item.name}</h5>
                  <p className="mt-1 line-clamp-1 text-[12px] text-slate-400">
                    {item.isAiCustom ? 'AI 专属高定配置' : item.desc || '京礼推荐心意之选'}
                  </p>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-[14px] font-black text-[#e4393c]">{formatYuan(item.price)}</span>
                  <button
                    onClick={() => handleRemoveOne(item.productId)}
                    disabled={busyId !== null}
                    className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] text-slate-400 transition hover:bg-[#fff0f2] hover:text-[#e4393c] disabled:opacity-40"
                  >
                    <Icon name="x" className="h-3 w-3" />
                    <span>移除</span>
                  </button>
                </div>
              </div>
            </div>
          ))}

          <div className="mt-6 space-y-2 rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
            <div className="flex justify-between text-[13px] text-slate-500">
              <span>小计</span>
              <span className="font-semibold text-slate-700">{formatYuan(subtotal)}</span>
            </div>
            <div className="flex justify-between text-[15px] font-black text-slate-950">
              <span>总额</span>
              <span>{formatYuan(subtotal)}</span>
            </div>
          </div>

          <button
            onClick={() => navigate('/v2/checkout')}
            className="w-full rounded-2xl bg-gradient-to-r from-[#e4393c] to-[#e4393c] py-3.5 text-center text-[15px] font-black text-white shadow-lg transition active:scale-95"
          >
            提交订单
          </button>
        </div>
      )}
    </div>
  );
}
