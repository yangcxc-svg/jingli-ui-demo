/**
 * v2 送礼诊断画像配置器：4 个问题 → 调用 generateRecommendations → 跳到 /v2/recommendations
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Icon } from '../components/Icon';
import { generateRecommendations } from '../api/v2Api';
import { useV2 } from '../state/V2Context';

const RELATIONS = [
  { label: '伴侣/恋人', value: '恋人', emoji: '玫瑰' },
  { label: '长辈/父母', value: '长辈', emoji: '家' },
  { label: '知心好友', value: '死党', emoji: '干杯' },
  { label: '职场伙伴', value: '同事', emoji: '公文包' },
  { label: '可爱宝贝', value: '孩子', emoji: '宝宝' },
  { label: '授业/恩师', value: '老师', emoji: '学士帽' },
];

const OCCASIONS = ['新婚之喜', '生日惊喜', '节日送礼', '乔迁新居', '探望长辈'];
const BUDGETS = [150, 500, 1500, 3000];
const ALL_TAGS = ['科技控', '文艺小资', '实用主义', '户外运动', '猫奴狗党', '美食饕餮', '极简生活', '二次元'];

const relationEmoji: Record<string, string> = {
  玫瑰: '🌹',
  家: '🏡',
  干杯: '🍻',
  公文包: '💼',
  宝宝: '👶',
  学士帽: '🎓',
};

const ageFromWizard = (age: string) => {
  const matched = age.match(/\d+/);
  return matched ? Number(matched[0]) : 31;
};

export default function V2WizardPage() {
  const navigate = useNavigate();
  const {
    wizard,
    setWizard,
    toggleTag,
    setRecommendations,
    triggerIsland,
    showToast,
  } = useV2();
  const [isGenerating, setIsGenerating] = useState(false);
  const selectedAge = ageFromWizard(wizard.age);
  const selectedOccasion = OCCASIONS[0];

  const handleGenerate = async () => {
    if (isGenerating) return;
    setIsGenerating(true);
    try {
      const result = await generateRecommendations(wizard);
      setRecommendations(result);
      if (result.recommendations.length === 0) {
        showToast('没有匹配商品，可放宽筛选条件再试');
      } else {
        triggerIsland('💡 灵感生成成功!', `已匹配 ${result.recommendations.length} 个真实商品方案`);
        navigate('/v2/recommendations');
      }
    } catch (err) {
      showToast(`接口出错: ${(err as Error).message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-full bg-[#f8f9fb] px-5 pb-7 pt-4 text-[#111827] animate-fadeIn">
      <div className="mb-4 flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate('/v2/home')}
          className="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-white hover:text-slate-900"
        >
          <Icon name="chevron-left" className="h-[18px] w-[18px]" />
        </button>
        <div className="rounded-full bg-[#fff0f2] px-3.5 py-1.5 text-[10px] font-black tracking-wide text-[#ff3f63] shadow-sm">
          ✨ Gemini 3.5 专家模式
        </div>
        <div className="w-8" />
      </div>

      <header className="mb-5 border-b border-slate-200 pb-4 text-center">
        <h1 className="text-[20px] font-black tracking-tight text-slate-950">心意智能订制</h1>
        <p className="mt-2 text-[10px] font-semibold leading-5 text-slate-400">
          录入 Ta 的专属画像，我们为您调遣供应链与 AI 艺术设计
        </p>
      </header>

      <div className="space-y-4">
        <section>
          <h2 className="mb-2.5 text-[13px] font-black text-slate-700">1. 送给谁?</h2>
          <div className="grid grid-cols-3 gap-2">
            {RELATIONS.map((rel) => (
              <button
                type="button"
                key={rel.value}
                onClick={() => setWizard({ relation: rel.value })}
                  className={`h-9 rounded-xl border text-[10px] font-black transition-all ${
                  wizard.relation === rel.value
                    ? 'border-[#ff3f63] bg-white text-[#ff3f63] shadow-sm'
                    : 'border-slate-200 bg-white text-slate-600 shadow-sm hover:border-slate-300'
                }`}
              >
                {rel.label} <span className="text-[10px]">{relationEmoji[rel.emoji]}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-100 bg-[#f5f8fb] px-4 py-3.5 shadow-sm">
          <div className="mb-2.5 flex items-center justify-between">
            <h2 className="text-[13px] font-black text-slate-700">2. 对方年龄:</h2>
            <span className="rounded-full bg-white px-3 py-1 text-[11px] font-black text-[#ff3f63] shadow-sm">
              {selectedAge} 岁
            </span>
          </div>
          <input
            type="range"
            min={18}
            max={70}
            step={1}
            value={selectedAge}
            onChange={(e) => setWizard({ age: `${e.target.value}岁` })}
            className="w-full accent-[#ff3f63]"
          />
        </section>

        <section>
          <h2 className="mb-2.5 text-[13px] font-black text-slate-700">3. 赠送场合:</h2>
          <button
            type="button"
            className="flex h-11 w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-4 text-left text-[12px] font-bold text-slate-700 shadow-sm"
          >
            <span>{selectedOccasion} 💍</span>
            <span className="text-lg leading-none text-slate-500">⌄</span>
          </button>
        </section>

        <section>
          <div className="mb-2.5 flex items-center justify-between">
            <h2 className="text-[13px] font-black text-slate-700">4. 预算范围 (元):</h2>
            <span className="text-[12px] font-black text-[#ff3f63]">¥{wizard.budget}</span>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {BUDGETS.map((budget) => (
              <button
                type="button"
                key={budget}
                onClick={() => setWizard({ budget })}
                className={`h-9 rounded-xl border text-[10px] font-black transition-all ${
                  wizard.budget === budget
                    ? 'border-[#ff3f63] bg-white text-[#ff3f63] shadow-sm'
                    : 'border-slate-200 bg-white text-slate-600 shadow-sm hover:border-slate-300'
                }`}
              >
                {budget === 3000 ? '奢华精选' : `¥${budget}`}
              </button>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-2.5 text-[13px] font-black text-slate-700">5. 标签画像 (最多3个):</h2>
          <div className="flex flex-wrap gap-2">
            {ALL_TAGS.map((tag) => {
              const active = wizard.tags.includes(tag);
              return (
                <button
                  type="button"
                  key={tag}
                  onClick={() => {
                    if (!active && wizard.tags.length >= 3) {
                      showToast('最多选择 3 个标签');
                      return;
                    }
                    toggleTag(tag);
                  }}
                  className={`rounded-full px-3.5 py-1.5 text-[10px] font-bold transition-all ${
                    active
                      ? 'bg-[#f59e0b] text-white shadow-sm'
                      : 'bg-[#edf2f7] text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </section>

        <section>
          <h2 className="mb-2.5 text-[13px] font-black text-slate-700">6. 特殊背景补充 (如需要):</h2>
          <textarea
            value={wizard.background}
            onChange={(e) => setWizard({ background: e.target.value })}
            className="min-h-[72px] w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-[11px] font-semibold leading-5 text-slate-700 shadow-sm outline-none placeholder:text-slate-400 focus:border-[#ff3f63]"
            placeholder="如：Ta 最近睡眠质量较差，爱猫咪..."
          />
        </section>

        <div className="pt-1">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating}
            className="flex h-11 w-full items-center justify-center space-x-2 rounded-2xl bg-gradient-to-r from-[#ff3f63] via-[#ff6b35] to-[#f59e0b] text-[12px] font-black text-white shadow-[0_14px_28px_rgba(255,63,99,0.2)] transition-transform active:scale-95 hover:opacity-95"
          >
            <Icon
              name="sparkles"
              className={`h-3.5 w-3.5 ${isGenerating ? 'animate-spin' : ''}`}
            />
            <span>{isGenerating ? 'AI 正在定制专属好物' : '立即定制 AI 专属好物'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
