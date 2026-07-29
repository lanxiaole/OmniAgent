import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

// highlight.js 主题：默认使用 GitHub 主题，在深色模式下通过 CSS 变量覆盖
import 'highlight.js/styles/github.css';

// 全局样式
import '@/styles/variables.css';
import '@/styles/base.css';
import '@/styles/animations.css';

import App from './App.vue';
import router from './router';

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(ElementPlus);

app.mount('#app');
