import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AnalysisView from '../views/AnalysisView.vue'
import DatabaseView from '../views/DatabaseView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/home' },
    { path: '/home', name: 'home', component: HomeView },
    { path: '/analysis', name: 'analysis', component: AnalysisView },
    { path: '/database', name: 'database', component: DatabaseView },
    { path: '/about', name: 'about', component: () => import('../views/AboutView.vue') },
  ],
})
export default router
