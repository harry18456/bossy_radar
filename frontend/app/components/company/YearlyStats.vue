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
import { Bar, Line, Chart } from 'vue-chartjs'
import { LineController, BarController } from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
  LineElement,
  LineController,
  PointElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps<{
  stats: any[] // NonManagerSalary[]
}>()

const sortedStats = computed(() => {
  return [...props.stats].sort((a, b) => a.year - b.year)
})

const isDark = useDark()

// Chart Configuration
const chartOptions = computed<any>(() => ({
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
        color: isDark.value ? '#94a3b8' : '#64748b',
        callback: (value: any) => value.toLocaleString()
      }
    }
  }
}))

// EPS Data
const epsData = computed(() => ({
  labels: sortedStats.value.map(s => s.year + '年'),
  datasets: [
    {
      label: 'EPS (每股盈餘)',
      data: sortedStats.value.map(s => s.eps),
      backgroundColor: '#3b82f6',
      borderRadius: 4,
      order: 2
    },
    {
      label: '同產業平均 EPS',
      data: sortedStats.value.map(s => s.industry_avg_eps),
      borderColor: '#94a3b8',
      backgroundColor: '#94a3b8',
      borderDash: [5, 5],
      type: 'line' as const,
      pointStyle: 'circle',
      pointRadius: 4,
      fill: false,
      order: 1
    }
  ]
}))

// Salary Data
const salaryData = computed(() => ({
  labels: sortedStats.value.map(s => s.year + '年'),
  datasets: [
    {
      label: '非主管平均薪資 (仟元)',
      data: sortedStats.value.map(s => s.avg_salary),
      borderColor: '#22c55e', // Green
      backgroundColor: '#22c55e',
      type: 'line' as const,
      yAxisID: 'y'
    },
    {
      label: '非主管中位數薪資 (仟元)',
      data: sortedStats.value.map(s => s.median_salary),
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
    <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm">
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">歷年 EPS 趨勢</h3>
      <div class="h-64">
        <Chart type="bar" :data="epsData" :options="chartOptions" />
      </div>
    </div>

    <!-- Salary Chart -->
    <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm">
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">非主管薪資趨勢</h3>
      <div class="h-64">
        <Line :data="salaryData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>
