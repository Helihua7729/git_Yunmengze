 

// 添加新的引入
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 在创建应用时使用
import { createApp } from 'vue'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')