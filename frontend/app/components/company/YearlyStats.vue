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
    },
    {
      label: '同業平均薪資 (仟元)',
      data: sortedStats.value.map(s => s.industry_avg_salary),
      borderColor: '#94a3b8', // Gray
      backgroundColor: '#94a3b8',
      borderDash: [5, 5],
      type: 'line' as const,
      pointStyle: 'circle',
      pointRadius: 4,
      yAxisID: 'y',
      order: 1
    }
  ]
}))
</script>

<template>
  <!-- Warning Alerts -->
  <div v-if="sortedStats.some(s => ['Y', 'V'].includes(s.is_avg_salary_under_500k || '') || ['Y', 'V'].includes(s.is_better_eps_lower_salary || '') || ['Y', 'V'].includes(s.is_eps_growth_salary_decrease || ''))" class="mb-6 space-y-3">
    <div v-for="stat in sortedStats" :key="stat.year">
       <template v-if="['Y', 'V'].includes(stat.is_avg_salary_under_500k || '') || ['Y', 'V'].includes(stat.is_better_eps_lower_salary || '') || ['Y', 'V'].includes(stat.is_eps_growth_salary_decrease || '')">
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
            <Icon name="lucide:alert-triangle" class="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
            <div>
              <h4 class="font-bold text-red-800 dark:text-red-300 text-sm mb-1">
                {{ stat.year }}年度 薪資警示
              </h4>
              <ul class="list-disc list-inside text-sm text-red-700 dark:text-red-400 space-y-1">
                <li v-if="['Y', 'V'].includes(stat.is_avg_salary_under_500k || '')">
                  基層平均年薪未達 50 萬
                </li>
                <li v-if="['Y', 'V'].includes(stat.is_better_eps_lower_salary || '')">
                  EPS 優於同業，薪資卻低於同業水準
                </li>
                <li v-if="['Y', 'V'].includes(stat.is_eps_growth_salary_decrease || '')">
                  EPS 較去年成長，薪資卻不升反降
                </li>
              </ul>
            </div>
          </div>
       </template>

       <!-- Company Notes -->
       <template v-if="stat.performance_salary_relation_note || stat.improvement_measures_note">
          <div class="bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg p-4 text-sm mt-3">
            <div class="flex items-center gap-2 mb-2 text-gray-900 dark:text-gray-100 font-medium">
              <Icon name="lucide:info" class="w-4 h-4 text-blue-500" />
              <span>{{ stat.year }}年度 公司補充說明</span>
            </div>
            
            <div v-if="stat.performance_salary_relation_note" class="mb-3 last:mb-0">
              <span class="block text-xs text-gray-500 dark:text-slate-400 mb-1">經營績效與薪酬之關聯性與合理性：</span>
              <p class="text-gray-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
                {{ stat.performance_salary_relation_note }}
              </p>
            </div>

            <div v-if="stat.improvement_measures_note">
              <span class="block text-xs text-gray-500 dark:text-slate-400 mb-1">未來改善措施：</span>
              <p class="text-gray-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
                {{ stat.improvement_measures_note }}
              </p>
            </div>
          </div>
       </template>
    </div>
  </div>

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
