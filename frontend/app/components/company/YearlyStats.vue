<script setup lang="ts">
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  type ChartOptions
} from 'chart.js'
import { Bar, Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps<{
  stats: any[] // YearlySummaryItem
}>()

const isDark = useDark()

// Chart Configuration
const chartOptions = computed<ChartOptions<'bar' | 'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        color: isDark.value ? '#e2e8f0' : '#475569'
      }
    },
    tooltip: {
      mode: 'index',
      intersect: false,
    }
  },
  scales: {
    x: {
      grid: {
        color: isDark.value ? '#334155' : '#e2e8f0'
      },
      ticks: {
        color: isDark.value ? '#94a3b8' : '#64748b'
      }
    },
    y: {
      grid: {
        color: isDark.value ? '#334155' : '#e2e8f0'
      },
      ticks: {
        color: isDark.value ? '#94a3b8' : '#64748b'
      }
    }
  }
}))

// EPS Data
const epsData = computed(() => ({
  labels: props.stats.map(s => s.year + '年'),
  datasets: [
    {
      label: 'EPS (每股盈餘)',
      data: props.stats.map(s => s.eps),
      backgroundColor: '#3b82f6',
      borderRadius: 4
    }
  ]
}))

// Salary Data
const salaryData = computed(() => ({
  labels: props.stats.map(s => s.year + '年'),
  datasets: [
    {
      label: '非主管平均薪資',
      data: props.stats.map(s => s.avg_salary_non_manager),
      borderColor: '#22c55e', // Green
      backgroundColor: '#22c55e',
      type: 'line' as const,
      yAxisID: 'y'
    },
    {
      label: '非主管中位數薪資',
      data: props.stats.map(s => s.median_salary_non_manager),
      borderColor: '#eab308', // Yellow
      backgroundColor: '#eab308',
      type: 'line' as const,
      yAxisID: 'y'
    }
  ]
}))
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <!-- EPS Chart -->
    <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">歷年 EPS 趨勢</h3>
      <div class="h-64">
        <Bar :data="epsData" :options="chartOptions" />
      </div>
    </div>

    <!-- Salary Chart -->
    <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">非主管薪資趨勢</h3>
      <div class="h-64">
        <Line :data="salaryData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>
