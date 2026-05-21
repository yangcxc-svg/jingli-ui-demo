/**
 * v2 支付成功页：与整体浅色清爽风格统一。
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { Icon } from '../components/Icon';
import { useV2 } from '../state/V2Context';

const formatYuan = (n: number) => `¥${Math.round(n).toLocaleString('zh-CN')}`;

export default function V2OrderSuccessPage() {
  const navigate = useNavigate();
  const { latestOrder, triggerIsland } = useV2();

  useEffect(() => {
    if (!latestOrder) return;
    triggerIsland('订单已支付', `单号 ${latestOrder.orderId}`, 5000);
  }, [latestOrder, triggerIsland]);

  if (!latestOrder) {
    return (
      <div className="flex min-h-full flex-col items-center justify-center bg-[#f8f9fb] px-6 py-20 text-slate-500">
        <p className="text-[14px]">暂无订单数据</p>
        <button
          onClick={() => navigate('/v2/home')}
          className="mt-4 text-[12px] font-bold text-[#e4393c] underline underline-offset-4"
        >
          返回首页
        </button>
      </div>
    );
  }

  const { orderId, items, totalAmount, needLuxuryBox, needAudioQR, address } = latestOrder;

  return (
    <div className="min-h-full bg-[#f8f9fb] px-4 pb-24 pt-6 text-slate-950 animate-fadeIn">
      {/* 顶部庆祝 */}
      <div className="mb-6 text-center">
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-[#fff0f2]">
          <Icon name="check" className="h-7 w-7 text-[#e4393c]" />
        </div>
        <h1 className="text-[22px] font-black text-slate-950">订单支付成功</h1>
        <p className="mt-1 text-[12px] text-slate-400">单号：{orderId}</p>
        <p className="mt-1 text-[18px] font-black text-[#e4393c]">{formatYuan(totalAmount)}</p>
      </div>

      <div className="space-y-4">
        {/* 语音二维码卡片 */}
        {needAudioQR && (
          <div className="rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
            <div className="mb-3 flex items-center gap-1.5">
              <Icon name="qr-code" className="h-4 w-4 text-[#e4393c]" />
              <span className="text-[12px] font-bold tracking-wider text-[#e4393c]">
                配音卡片二维码已随件印发
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative flex h-20 w-20 shrink-0 items-center justify-center rounded-xl bg-white p-1.5 shadow-sm ring-1 ring-slate-100">
                <svg className="h-full w-full text-slate-900" viewBox="0 0 100 100">
                  <rect x="0" y="0" width="30" height="30" fill="currentColor" />
                  <rect x="5" y="5" width="20" height="20" fill="white" />
                  <rect x="10" y="10" width="10" height="10" fill="currentColor" />
                  <rect x="70" y="0" width="30" height="30" fill="currentColor" />
                  <rect x="75" y="5" width="20" height="20" fill="white" />
                  <rect x="80" y="10" width="10" height="10" fill="currentColor" />
                  <rect x="0" y="70" width="30" height="30" fill="currentColor" />
                  <rect x="5" y="75" width="20" height="20" fill="white" />
                  <rect x="10" y="80" width="10" height="10" fill="currentColor" />
                  <path d="M 40,10 H 50 V 20 H 40 Z" fill="currentColor" />
                  <path d="M 10,40 H 20 V 50 H 10 Z" fill="currentColor" />
                  <path d="M 50,40 H 60 V 60 H 50 Z" fill="currentColor" />
                  <path d="M 80,40 H 90 V 60 H 80 Z" fill="currentColor" />
                  <path d="M 40,70 H 60 V 80 H 40 Z" fill="currentColor" />
                  <path d="M 70,70 H 90 V 90 H 70 Z" fill="currentColor" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex h-5 w-5 items-center justify-center rounded-md border border-indigo-500/50 bg-black">
                    <Icon name="mic" className="h-2.5 w-2.5 text-indigo-400" />
                  </div>
                </div>
              </div>
              <div className="flex-1">
                <p className="text-[14px] font-black text-slate-950">收信人扫一扫听到你</p>
                <p className="mt-1 text-[12px] leading-relaxed text-slate-500">
                  拆礼盒时扫描贺卡，即可听到你的语音祝福。
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 礼物清单 */}
        <div className="rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-[12px] font-bold tracking-wider text-slate-500">
              本单礼物（{items.length}）
            </span>
            {needLuxuryBox && (
              <span className="rounded-full bg-[#fff0f2] px-2 py-0.5 text-[11px] font-black text-[#e4393c]">
                奢华礼盒
              </span>
            )}
          </div>
          <ul className="space-y-2">
            {items.map((it, idx) => (
              <li
                key={`${it.productId}-${idx}`}
                className="flex items-center justify-between text-[12px]"
              >
                <span className="truncate text-slate-700">{it.name}</span>
                <span className="font-black text-slate-950">{formatYuan(it.price)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3">
            <span className="text-[12px] font-bold text-slate-500">总计</span>
            <span className="text-[16px] font-black text-[#e4393c]">{formatYuan(totalAmount)}</span>
          </div>
        </div>

        {/* 分享卡片 */}
        <div className="rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
          <div className="mb-3 flex items-center gap-1.5">
            <Icon name="gift" className="h-4 w-4 text-[#e4393c]" />
            <span className="text-[12px] font-bold tracking-wider text-[#e4393c]">
              分享给朋友填写收礼地址
            </span>
          </div>
          <p className="mb-3 text-[12px] leading-relaxed text-slate-500">
            好友通过链接填写地址后自动发货，可在订单详情查看进度。
          </p>
          <div className="mb-3 flex items-center gap-2">
            <div className="flex-1 overflow-hidden rounded-lg bg-slate-50 px-3 py-2 text-[12px] text-slate-500">
              <span className="truncate">https://jingli.ai/share/{orderId}</span>
            </div>
            <button
              onClick={() => {
                navigator.clipboard?.writeText(`https://jingli.ai/share/${orderId}`);
                triggerIsland('链接已复制', '快去微信粘贴分享给好友吧', 3000);
              }}
              className="shrink-0 rounded-lg bg-[#fff0f2] px-3 py-2 text-[11px] font-black text-[#e4393c] transition hover:bg-rose-100"
            >
              复制链接
            </button>
          </div>
          <button
            onClick={() => triggerIsland('已唤起微信', '请选择要分享的好友', 3000)}
            className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-[#e4393c] to-[#e4393c] py-2.5 text-[13px] font-black text-white shadow-md transition active:scale-[0.98]"
          >
            <Icon name="message-circle" className="h-3.5 w-3.5" />
            分享到微信
          </button>
        </div>

        {/* 物流轨迹 */}
        <div className="rounded-[18px] bg-white p-4 shadow-sm ring-1 ring-slate-100">
          <span className="mb-2 block text-[12px] font-bold tracking-wider text-slate-500">
            物流轨迹
          </span>
          <div className="flex items-center gap-2 text-[12px]">
            <div className="h-1.5 w-1.5 shrink-0 animate-ping rounded-full bg-[#e4393c]" />
            <span className="font-bold text-[#e4393c]">
              京东快递揽件中：{address.fullAddress.split(' ')[0] || '浙江省杭州市西湖区'}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-2 text-[12px] text-slate-500">
            <Icon name="truck" className="h-3.5 w-3.5" />
            <span>预计 24h 内由京东快递特快配送至：{address.recipient} {address.phone}</span>
          </div>
        </div>

        {/* 返回首页 */}
        <button
          onClick={() => navigate('/v2/home')}
          className="w-full rounded-2xl bg-white py-3 text-center text-[13px] font-bold text-slate-700 shadow-sm ring-1 ring-slate-100 transition hover:bg-slate-50 active:scale-[0.98]"
        >
          返回首页尊享阁
        </button>
      </div>
    </div>
  );
}
