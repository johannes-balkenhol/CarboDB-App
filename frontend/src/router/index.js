import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import HmmerSearchView from '@/views/HmmerSearchView.vue'
import AllSearchesView from '@/views/AllSearchesView.vue'
import AnalysisView from '@/views/AnalysisView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/home'
    },
    {
      path: '/home',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/hmmer-search',
      name: 'hmmer-search',
      component: HmmerSearchView,
    },
    {
      path: '/all-searches',
      name: 'all-searches',
      component: AllSearchesView,
    },
    {
      path: '/analysis',
      name: 'analysis',
      component: AnalysisView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

export default router
