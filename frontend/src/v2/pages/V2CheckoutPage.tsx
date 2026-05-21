/**
 * v2 送礼结账台：送朋友流程（下单支付 → 定制贺卡 → 朋友收礼）。
 * 支付按钮：先调后端 checkout-preview 确认金额，然后本地生成订单并跳转。
 */
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Icon } from '../components/Icon';
import { useV2 } from '../state/V2Context';
import { previewV2Checkout, removeV2CartItem } from '../api/v2CartApi';

const formatYuan = (n: number) => `¥${Math.round(n).toLocaleString('zh-CN')}`;

const LUXURY_BOX_FEE = 68;

export default function V2CheckoutPage() {
  const navigate = useNavigate();
  const {
    cartItems,
    setCartItems,
    address,
    needLuxuryBox,
    setNeedLuxuryBox,
    needAudioQR,
    setNeedAudioQR,
    placeOrder,
    showToast,
  } = useV2();

  const [submitting, setSubmitting] = useState(false);
  const [addressMode, setAddressMode] = useState<'self' | 'friend'>('self');
  const [showAllGifts, setShowAllGifts] = useState(false);

  const subtotal = useMemo(() => cartItems.reduce((s, it) => s + it.price, 0), [cartItems]);
  const packagingFee = needLuxuryBox ? LUXURY_BOX_FEE : 0;
  const discount = 0; // 占位：官方直降
  const couponDiscount = 0; // 占位：优惠券
  const totalAmount = subtotal + packagingFee - discount - couponDiscount;

  async function handlePay() {
    if (cartItems.length === 0) {
      showToast('购物车为空，请先添加心仪礼物');
      return;
    }
    setSubmitting(true);
    try {
      const preview = await previewV2Checkout(cartItems);
      if (preview && preview.unavailable_product_ids.length > 0) {
        showToast(`有 ${preview.unavailable_product_ids.length} 件商品暂不可结算`);
        setSubmitting(false);
        return;
      }

      const snapshot = [...cartItems];
      placeOrder({ items: snapshot, subtotal });

      const uniqueIds = Array.from(new Set(cartItems.map((it) => it.productId)));
      let next = cartItems;
      for (const productId of uniqueIds) {
        next = await removeV2CartItem(productId);
      }
      setCartItems(next);

      navigate('/v2/order-success', { replace: true });
    } catch (err) {
      console.error(err);
      showToast('支付失败，请稍后再试');
    } finally {
      setSubmitting(false);
    }
  }

  const displayGifts = showAllGifts ? cartItems : cartItems.slice(0, 1);

  return (
    <div className="min-h-full bg-[#f8f9fb] px-4 pb-28 pt-2 text-slate-950 animate-fadeIn">
      {/* 顶部导航 */}
      <div className="mb-4 flex items-center justify-between">
        <button
          onClick={() => navigate('/v2/cart')}
          className="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-white"
        >
          <Icon name="chevron-left" className="h-5 w-5" />
        </button>
        <span className="text-[15px] font-black text-slate-900">送朋友</span>
        <div className="w-8" />
      </div>

      {/* 步骤条 */}
      <div className="mb-5 flex items-center justify-center rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-slate-100">
        <div className="flex items-center gap-1.5 text-[10px]">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#ff3f63] text-[9px] font-black text-white">1</span>
          <span className="font-black text-[#ff3f63]">下单支付</span>
          <span className="mx-1 text-slate-300">›</span>
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-[9px] font-black text-slate-400">2</span>
          <span className="font-semibold text-slate-400">定制贺卡并分享</span>
          <span className="mx-1 text-slate-300">›</span>
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-[9px] font-black text-slate-400">3</span>
          <span className="font-semibold text-slate-400">朋友收礼</span>
        </div>
      </div>

      {/* 地址选择 */}
      <div className="mb-4 space-y-2.5">
        <button
          onClick={() => setAddressMode('friend')}
          className={`flex w-full items-center justify-between rounded-2xl px-4 py-3.5 text-left transition ${
            addressMode === 'friend'
              ? 'bg-[#fff0f2] ring-1 ring-[#ff3f63]/20'
              : 'bg-white shadow-sm ring-1 ring-slate-100'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <div className={`flex h-6 w-6 items-center justify-center rounded-full ${addressMode === 'friend' ? 'bg-[#ff3f63]' : 'bg-slate-200'}`}>
              <Icon name="gift" className={`h-3 w-3 ${addressMode === 'friend' ? 'text-white' : 'text-slate-500'}`} />
            </div>
            <span className={`text-[13px] font-black ${addressMode === 'friend' ? 'text-[#ff3f63]' : 'text-slate-700'}`}>
              朋友选地址
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[11px] text-slate-400">付款后分享好友填地址</span>
            <Icon name="info" className="h-3.5 w-3.5 text-slate-300" />
          </div>
        </button>

        <button
          onClick={() => setAddressMode('self')}
          className={`flex w-full items-center justify-between rounded-2xl px-4 py-3.5 text-left transition ${
            addressMode === 'self'
              ? 'bg-[#fff0f2] ring-1 ring-[#ff3f63]/20'
              : 'bg-white shadow-sm ring-1 ring-slate-100'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <div className={`flex h-6 w-6 items-center justify-center rounded-full ${addressMode === 'self' ? 'bg-[#ff3f63]' : 'bg-slate-200'}`}>
              <Icon name="map-pin" className={`h-3 w-3 ${addressMode === 'self' ? 'text-white' : 'text-slate-500'}`} />
            </div>
            <span className={`text-[13px] font-black ${addressMode === 'self' ? 'text-[#ff3f63]' : 'text-slate-700'}`}>
              我选地址
            </span>
          </div>
          {addressMode === 'self' ? (
            <span className="text-[11px] text-slate-400">
              {address.recipient} {address.phone.slice(0, 3)}****{address.phone.slice(-4)}
            </span>
          ) : (
            <span className="text-[11px] text-slate-400">选择收礼地址 ›</span>
          )}
        </button>
      </div>

      {/* 礼物 */}
      <div className="mb-4 rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
        <h3 className="mb-3 text-[13px] font-black text-slate-900">礼物</h3>
        {cartItems.length === 0 ? (
          <p className="py-4 text-center text-[11px] text-slate-400">购物车为空</p>
        ) : (
          <div className="space-y-4">
            {displayGifts.map((it, idx) => (
              <div key={`${it.productId}-${idx}`} className="flex gap-3">
                <div className="h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-slate-50">
                  {it.imageUrl ? (
                    <img src={it.imageUrl} alt={it.name} className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <Icon name="image" className="h-6 w-6 text-slate-300" />
                    </div>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-black leading-snug text-slate-900 line-clamp-2">{it.name}</p>
                  <p className="mt-1 text-[11px] text-slate-400 line-clamp-1">{it.desc}</p>
                  <p className="mt-2 text-[14px] font-black text-[#ff3f63]">{formatYuan(it.price)}</p>
                </div>
              </div>
            ))}
            {cartItems.length > 1 && (
              <button
                onClick={() => setShowAllGifts((v) => !v)}
                className="mx-auto flex items-center gap-1 rounded-full bg-slate-50 px-4 py-1.5 text-[11px] font-semibold text-slate-500 transition hover:bg-slate-100"
              >
                {showAllGifts ? '收起' : `全部 ${cartItems.length} 件`}
                <Icon name="chevron-left" className={`h-3 w-3 transition ${showAllGifts ? '-rotate-90' : 'rotate-[-90deg]'}`} />
              </button>
            )}
          </div>
        )}
      </div>

      {/* 费用明细 */}
      <div className="mb-4 rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
        <div className="space-y-3 text-[12px]">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">商品金额</span>
            <span className="font-semibold text-slate-700">{formatYuan(subtotal)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">运费</span>
            <span className="font-semibold text-emerald-500">免运费</span>
          </div>
          {needLuxuryBox && (
            <div className="flex items-center justify-between">
              <span className="text-slate-500">高级绒礼包装</span>
              <span className="font-semibold text-slate-700">+{formatYuan(LUXURY_BOX_FEE)}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-slate-500">官方直降</span>
            <span className="font-semibold text-[#ff3f63]">-{formatYuan(discount)}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">优惠券</span>
              <span className="rounded bg-[#fff0f2] px-1.5 py-0.5 text-[9px] font-black text-[#ff3f63]">已选推荐优惠</span>
            </div>
            <span className="font-semibold text-[#ff3f63]">-{formatYuan(couponDiscount)}</span>
          </div>
          <div className="flex items-center justify-between border-t border-slate-100 pt-3">
            <span className="text-[13px] font-black text-slate-700">合计</span>
            <span className="text-[16px] font-black text-[#ff3f63]">{formatYuan(totalAmount)}</span>
          </div>
        </div>
      </div>

      {/* 定制服务（对应步骤2 定制贺卡） */}
      <div className="mb-4 rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
        <h3 className="mb-3 text-[13px] font-black text-slate-900">定制服务</h3>
        <div className="space-y-3">
          <label className="flex cursor-pointer items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-50">
                <Icon name="box" className="h-4 w-4 text-slate-400" />
              </div>
              <div>
                <p className="text-[12px] font-bold text-slate-700">手工奢华深空绒皮礼盒</p>
                <p className="text-[10px] text-slate-400">配套香薰干花与纯金丝带寄语</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={needLuxuryBox}
              onChange={(e) => setNeedLuxuryBox(e.target.checked)}
              className="h-5 w-5 accent-[#ff3f63]"
            />
          </label>
          <label className="flex cursor-pointer items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-50">
                <Icon name="qr-code" className="h-4 w-4 text-slate-400" />
              </div>
              <div>
                <p className="text-[12px] font-bold text-slate-700">实体贺卡专属 AI 声音二维码</p>
                <p className="text-[10px] text-slate-400">实体包装上印专属二维码，扫码立听温暖语音</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={needAudioQR}
              onChange={(e) => setNeedAudioQR(e.target.checked)}
              className="h-5 w-5 accent-[#ff3f63]"
            />
          </label>
        </div>
      </div>

      {/* 底部支付栏 */}
      <div className="fixed bottom-16 left-4 right-4 z-50 rounded-2xl bg-white px-4 py-3 shadow-[0_-8px_32px_rgba(15,23,42,0.12)]">
        <div className="mx-auto max-w-md">
          <div className="mb-2 flex items-baseline gap-2">
            <span className="text-[22px] font-black text-[#ff3f63]">{formatYuan(totalAmount)}</span>
            <span className="text-[11px] text-slate-400">共减{formatYuan(discount + couponDiscount)}</span>
          </div>
          <div className="grid grid-cols-[1fr_1.6fr] gap-2">
            <button
              onClick={() => showToast('群送礼功能即将上线')}
              className="flex flex-col items-center justify-center rounded-xl bg-[#fff0f2] py-2.5 transition active:scale-95"
            >
              <span className="text-[13px] font-black text-[#ff3f63]">群送礼</span>
              <span className="text-[9px] text-[#ff3f63]/70">{cartItems.length}份礼物，每人抽一份</span>
            </button>
            <button
              onClick={handlePay}
              disabled={submitting || cartItems.length === 0}
              className="flex items-center justify-center rounded-xl bg-gradient-to-r from-[#ff3f63] to-[#ff6b35] text-[14px] font-black text-white shadow-lg transition active:scale-95 disabled:opacity-50"
            >
              {submitting ? '支付中...' : '付款并赠送'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
