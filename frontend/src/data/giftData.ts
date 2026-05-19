export const giftScenes = [
  { title: '生日礼物', icon: '🎂', desc: '朋友、同事、家人生日', active: true, budget: 500, target: '25岁女生/朋友/同事/家人', goal: '有心意、颜值高、不过度昂贵' },
  { title: '见家长', icon: '🏠', desc: '体面不出错', budget: 3000, target: '对象父母/长辈', goal: '正式、体面、稳妥、不冒犯' },
  { title: '情侣纪念日', icon: '💝', desc: '浪漫、有心意', budget: 1000, target: '恋人/伴侣', goal: '浪漫、有纪念意义、有惊喜感' },
  { title: '送领导/客户', icon: '🤝', desc: '稳重、有分寸', budget: 2000, target: '领导/客户/合作伙伴', goal: '稳重、有分寸、商务感、不越界' },
  { title: '乔迁新居', icon: '🏡', desc: '实用、有品质', budget: 1200, target: '乔迁新居的朋友/亲戚', goal: '实用、有品质、适合新家' },
  { title: '探望长辈', icon: '🍵', desc: '健康、实用', budget: 1000, target: '父母/长辈', goal: '健康、实用、表达关心' },
  { title: '婚礼/订婚', icon: '💍', desc: '喜庆、有档次', budget: 2000, target: '新婚/订婚朋友或亲人', goal: '喜庆、有档次、适合正式场合' },
  { title: '节日送礼', icon: '🎁', desc: '春节、中秋、端午', budget: 1500, target: '亲友/长辈/客户', goal: '节日氛围、体面、可分享' },
];

export const giftProducts = [
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

export const quickQuestions = ['送女朋友生日礼物', '见家长带什么合适', '送领导不尴尬', '给爸妈买健康礼物'];

export const comboProducts = [
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

export const valuePoints = [
  { title: '体面感', icon: '🎩', desc: '茶礼和滋补礼盒承担正式送礼属性，不显随意。', tone: 'bg-red-50 text-red-600' },
  { title: '实用性', icon: '💆', desc: '按摩仪体现对健康的关心，避免礼物只停留在表面。', tone: 'bg-violet-50 text-violet-600' },
  { title: '家庭共享', icon: '🥜', desc: '坚果礼盒适合全家一起享用，让礼物更自然。', tone: 'bg-amber-50 text-amber-700' },
];

export const comboChips = ['更高端', '更健康', '更稳妥', '控制在 2500 内', '增加科技感'];

export const premiumProducts = [
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

export const premiumValuePoints = [
  { title: '主礼更体面', icon: '🎩', desc: '茶礼和滋补礼盒提升正式感，适合长辈场景。', tone: 'bg-red-50 text-red-600' },
  { title: '健康关怀升级', icon: '💆', desc: '按摩仪 Pro 体现更高预算下的实用价值。', tone: 'bg-violet-50 text-violet-600' },
  { title: '兼顾全家感受', icon: '🥜', desc: '坚果礼盒适合家庭分享，降低送礼压迫感。', tone: 'bg-amber-50 text-amber-700' },
];

export const premiumChips = ['控制在 4000 内', '更健康', '更商务', '增加酒水', '更适合第一次见面'];

export const cartProducts = [
  { name: '高端茶礼礼盒', spec: '礼盒装｜长辈送礼｜体面稳妥', price: '¥699', icon: '🍵', tags: ['京礼推荐', '体面不出错'], tone: 'from-emerald-50 to-lime-100' },
  { name: '智能按摩仪', spec: '肩颈放松｜健康关怀', price: '¥899', icon: '💆', tags: ['健康实用', '长辈适合'], tone: 'from-sky-50 to-violet-100' },
  { name: '滋补养生礼盒', spec: '长辈养生｜正式送礼', price: '¥799', icon: '🎁', tags: ['有分量', '养生礼盒'], tone: 'from-red-50 to-orange-100' },
  { name: '品质坚果礼盒', spec: '全家共享｜补充搭配', price: '¥589', icon: '🥜', tags: ['家庭共享', '自然不尴尬'], tone: 'from-amber-50 to-yellow-100' },
];

