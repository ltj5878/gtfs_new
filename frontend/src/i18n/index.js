import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN.js'
import en from './en.js'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    en
  }
})

// 独立 t 函数，供 stores 等非组件代码使用
export const t = (key, ...args) => i18n.global.t(key, ...args)

export default i18n
