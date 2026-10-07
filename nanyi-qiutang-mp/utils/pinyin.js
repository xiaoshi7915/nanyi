/**
 * 汉字 -> 拼音（大写）映射表
 * 由线上品牌名语料生成，用于详情页副标题（如 寒影 -> HAN YING）
 * 字数：330
 */

const PINYIN_MAP = {
  '一': 'YI', '丁': 'DING', '万': 'WAN', '下': 'XIA', '不': 'BU', '丛': 'CONG', '东': 'DONG', '丝': 'SI',
  '中': 'ZHONG', '丸': 'WAN', '丹': 'DAN', '之': 'ZHI', '乳': 'RU', '事': 'SHI', '云': 'YUN', '五': 'WU',
  '井': 'JING', '亭': 'TING', '人': 'REN', '仙': 'XIAN', '令': 'LING', '何': 'HE', '佳': 'JIA', '信': 'XIN',
  '儿': 'ER', '兰': 'LAN', '凌': 'LING', '凤': 'FENG', '出': 'CHU', '十': 'SHI', '千': 'QIAN', '卉': 'HUI',
  '华': 'HUA', '南': 'NAN', '卿': 'QING', '原': 'YUAN', '去': 'QU', '双': 'SHUANG', '变': 'BIAN', '叠': 'DIE',
  '叶': 'YE', '叹': 'TAN', '合': 'HE', '同': 'TONG', '味': 'WEI', '品': 'PIN', '喜': 'XI', '嘉': 'JIA',
  '因': 'YIN', '园': 'YUAN', '国': 'GUO', '图': 'TU', '地': 'DI', '坐': 'ZUO', '堂': 'TANG', '塞': 'SAI',
  '墨': 'MO', '壳': 'KE', '多': 'DUO', '夜': 'YE', '天': 'TIAN', '夭': 'YAO', '夷': 'YI', '奉': 'FENG',
  '奶': 'NAI', '如': 'RU', '妃': 'FEI', '妙': 'MIAO', '姜': 'JIANG', '娇': 'JIAO', '娘': 'NIANG', '嫩': 'NEN',
  '宋': 'SONG', '宝': 'BAO', '客': 'KE', '宫': 'GONG', '寒': 'HAN', '寻': 'XUN', '山': 'SHAN', '岫': 'XIU',
  '峤': 'JIAO', '常': 'CHANG', '年': 'NIAN', '幻': 'HUAN', '底': 'DI', '庭': 'TING', '引': 'YIN', '彩': 'CAI',
  '影': 'YING', '心': 'XIN', '忘': 'WANG', '恋': 'LIAN', '意': 'YI', '才': 'CAI', '抹': 'MO', '招': 'ZHAO',
  '拾': 'SHI', '提': 'TI', '数': 'SHU', '旗': 'QI', '时': 'SHI', '星': 'XING', '春': 'CHUN', '晓': 'XIAO',
  '晚': 'WAN', '景': 'JING', '晴': 'QING', '暗': 'AN', '曲': 'QU', '月': 'YUE', '有': 'YOU', '木': 'MU',
  '未': 'WEI', '朱': 'ZHU', '杳': 'YAO', '杷': 'PA', '松': 'SONG', '枇': 'PI', '果': 'GUO', '枝': 'ZHI',
  '枫': 'FENG', '柑': 'GAN', '染': 'RAN', '柿': 'SHI', '栖': 'QI', '样': 'YANG', '格': 'GE', '桃': 'TAO',
  '梅': 'MEI', '梦': 'MENG', '梧': 'WU', '棘': 'JI', '榴': 'LIU', '橘': 'JU', '次': 'CI', '歌': 'GE',
  '正': 'ZHENG', '步': 'BU', '殷': 'YIN', '毒': 'DU', '水': 'SHUI', '汁': 'ZHI', '江': 'JIANG', '池': 'CHI',
  '汤': 'TANG', '沙': 'SHA', '沾': 'ZHAN', '波': 'BO', '洒': 'SA', '流': 'LIU', '浅': 'QIAN', '浓': 'NONG',
  '浦': 'PU', '浪': 'LANG', '涛': 'TAO', '深': 'SHEN', '清': 'QING', '渐': 'JIAN', '渠': 'QU', '湖': 'HU',
  '湛': 'ZHAN', '源': 'YUAN', '溶': 'RONG', '满': 'MAN', '澜': 'LAN', '火': 'HUO', '灰': 'HUI', '灵': 'LING',
  '烟': 'YAN', '热': 'RE', '照': 'ZHAO', '版': 'BAN', '牡': 'MU', '狂': 'KUANG', '玉': 'YU', '玫': 'MEI',
  '珍': 'ZHEN', '珠': 'ZHU', '琉': 'LIU', '瑞': 'RUI', '瑰': 'GUI', '璃': 'LI', '瓜': 'GUA', '瓞': 'DIE',
  '瓶': 'PING', '瓷': 'CI', '生': 'SHENG', '画': 'HUA', '留': 'LIU', '白': 'BAI', '百': 'BAI', '皎': 'JIAO',
  '看': 'KAN', '真': 'ZHEN', '眠': 'MIAN', '石': 'SHI', '砂': 'SHA', '碧': 'BI', '禄': 'LU', '福': 'FU',
  '秋': 'QIU', '端': 'DUAN', '竹': 'ZHU', '第': 'DI', '笺': 'JIAN', '篱': 'LI', '米': 'MI', '粉': 'FEN',
  '紫': 'ZI', '絮': 'XU', '红': 'HONG', '纹': 'WEN', '绢': 'JUAN', '绵': 'MIAN', '绿': 'LV', '缘': 'YUAN',
  '缨': 'YING', '罗': 'LUO', '羹': 'GENG', '羽': 'YU', '翠': 'CUI', '翡': 'FEI', '耕': 'GENG', '肉': 'ROU',
  '色': 'SE', '芋': 'YU', '芒': 'MANG', '芙': 'FU', '芝': 'ZHI', '芦': 'LU', '花': 'HUA', '芳': 'FANG',
  '芸': 'YUN', '苎': 'ZHU', '若': 'RUO', '茄': 'JIA', '茗': 'MING', '茶': 'CHA', '荆': 'JING', '草': 'CAO',
  '荷': 'HE', '莲': 'LIAN', '菂': 'DI', '菩': 'PU', '菲': 'FEI', '菽': 'SHU', '萄': 'TAO', '萝': 'LUO',
  '萧': 'XIAO', '萼': 'E', '葡': 'PU', '蓉': 'RONG', '蓝': 'LAN', '蓼': 'LIAO', '蔓': 'MAN', '蕉': 'JIAO',
  '蕊': 'RUI', '藕': 'OU', '藤': 'TENG', '藻': 'ZAO', '虫': 'CHONG', '蜜': 'MI', '蝶': 'DIE', '螺': 'LUO',
  '蟹': 'XIE', '蟾': 'CHAN', '衣': 'YI', '袅': 'NIAO', '袍': 'PAO', '裁': 'CAI', '西': 'XI', '观': 'GUAN',
  '计': 'JI', '设': 'SHE', '词': 'CI', '试': 'SHI', '豆': 'DOU', '豇': 'JIANG', '赤': 'CHI', '起': 'QI',
  '踏': 'TA', '身': 'SHEN', '辛': 'XIN', '进': 'JIN', '远': 'YUAN', '道': 'DAO', '酌': 'ZHUO', '酒': 'JIU',
  '酪': 'LAO', '醉': 'ZUI', '采': 'CAI', '釉': 'YOU', '里': 'LI', '金': 'JIN', '钓': 'DIAO', '钢': 'GANG',
  '钿': 'DIAN', '铜': 'TONG', '银': 'YIN', '锁': 'SUO', '锦': 'JIN', '问': 'WEN', '阳': 'YANG', '阿': 'A',
  '陵': 'LING', '雀': 'QUE', '雅': 'YA', '雨': 'YU', '雪': 'XUE', '霜': 'SHUANG', '霞': 'XIA', '霭': 'AI',
  '露': 'LU', '青': 'QING', '风': 'FENG', '飞': 'FEI', '饮': 'YIN', '香': 'XIANG', '魂': 'HUN', '鳞': 'LIN',
  '鹂': 'LI', '鹅': 'E', '鹊': 'QUE', '鹤': 'HE', '麟': 'LIN', '麻': 'MA', '黄': 'HUANG', '黑': 'HEI',
  '黛': 'DAI', '龙': 'LONG',
};

/**
 * 汉字转大写拼音，多个字以空格分隔
 * @param {string} text
 * @returns {string}
 */
function toPinyin(text) {
  if (!text) return '';
  const out = [];
  const str = String(text);
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if (PINYIN_MAP[ch]) {
      out.push(PINYIN_MAP[ch]);
    } else if (/[A-Za-z0-9]/.test(ch)) {
      out.push(ch.toUpperCase());
    }
  }
  return out.join(' ');
}

module.exports = { PINYIN_MAP, toPinyin };
