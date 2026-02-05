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
  type ChartOptions,
} from "chart.js";
import { Bar, Line, Chart } from "vue-chartjs";
import { LineController, BarController } from "chart.js";

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
  Legend,
);

const props = withDefaults(
  defineProps<{
    stats: any[]; // NonManagerSalary[]
    adjustments?: any[]; // SalaryAdjustment[]
  }>(),
  {
    stats: () => [],
    adjustments: () => [],
  },
);

const sortedStats = computed(() => {
  return [...props.stats].sort((a, b) => a.year - b.year);
});

const sortedAdjustments = computed(() => {
  return [...props.adjustments].sort((a, b) => a.year - b.year);
});

const isDark = useDark();

// Chart Configuration
const chartOptions = computed<any>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "top",
      labels: {
        color: isDark.value ? "#e2e8f0" : "#475569",
      },
    },
    tooltip: {
      mode: "index",
      intersect: false,
    },
  },
  scales: {
    x: {
      grid: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
    y: {
      grid: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
        callback: (value: any) => value.toLocaleString(),
      },
    },
  },
}));

// EPS Data
const epsData = computed(() => ({
  labels: sortedStats.value.map((s) => s.year + "年"),
  datasets: [
    {
      label: "EPS (每股盈餘)",
      data: sortedStats.value.map((s) => s.eps),
      backgroundColor: "#3b82f6",
      borderRadius: 4,
      order: 2,
    },
    {
      label: "同產業平均 EPS",
      data: sortedStats.value.map((s) => s.industry_avg_eps),
      borderColor: "#94a3b8",
      backgroundColor: "#94a3b8",
      borderDash: [5, 5],
      type: "line" as const,
      pointStyle: "circle",
      pointRadius: 4,
      fill: false,
      order: 1,
    },
  ],
}));

// Salary Data
const salaryData = computed(() => ({
  labels: sortedStats.value.map((s) => s.year + "年"),
  datasets: [
    {
      label: "非主管平均薪資 (仟元)",
      data: sortedStats.value.map((s) => s.avg_salary),
      borderColor: "#22c55e", // Green
      backgroundColor: "#22c55e",
      type: "line" as const,
      yAxisID: "y",
    },
    {
      label: "非主管中位數薪資 (仟元)",
      data: sortedStats.value.map((s) => s.median_salary),
      borderColor: "#eab308", // Yellow
      backgroundColor: "#eab308",
      type: "line" as const,
      yAxisID: "y",
    },
    {
      label: "同業平均薪資 (仟元)",
      data: sortedStats.value.map((s) => s.industry_avg_salary),
      borderColor: "#94a3b8", // Gray
      backgroundColor: "#94a3b8",
      borderDash: [5, 5],
      type: "line" as const,
      pointStyle: "circle",
      pointRadius: 4,
      yAxisID: "y",
      order: 1,
    },
  ],
}));

// Check if we have growth rate data
const hasGrowthData = computed(() => {
  return sortedStats.value.some(
    (s) => s.avg_salary_change != null || s.median_salary_change != null,
  );
});

// Salary Growth Rate Data
const salaryGrowthData = computed(() => ({
  labels: sortedStats.value.map((s) => s.year + "年"),
  datasets: [
    {
      label: "平均薪資成長率 (%)",
      data: sortedStats.value.map((s) => s.avg_salary_change),
      borderColor: "#22c55e",
      backgroundColor: "rgba(34, 197, 94, 0.1)",
      fill: true,
      tension: 0.3,
    },
    {
      label: "中位數薪資成長率 (%)",
      data: sortedStats.value.map((s) => s.median_salary_change),
      borderColor: "#eab308",
      backgroundColor: "rgba(234, 179, 8, 0.1)",
      fill: true,
      tension: 0.3,
    },
  ],
}));

// Growth rate chart options (with percentage display)
const growthChartOptions = computed<any>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "top",
      labels: {
        color: isDark.value ? "#e2e8f0" : "#475569",
      },
    },
    tooltip: {
      mode: "index",
      intersect: false,
      callbacks: {
        label: (context: any) => {
          const value = context.parsed.y;
          return `${context.dataset.label}: ${value?.toFixed(2) ?? "-"}%`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
    y: {
      grid: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
        callback: (value: any) => `${value}%`,
      },
    },
  },
}));

// Adjustment Data
const adjustmentData = computed(() => ({
  labels: sortedAdjustments.value.map((s) => s.year + "年"),
  datasets: [
    {
      label: "提撥金額 (元)",
      data: sortedAdjustments.value.map((s) => s.total_allocation_amount),
      backgroundColor: "#8b5cf6", // Violet
      borderRadius: 4,
    },
  ],
}));
</script>

<template>
  <!-- Warning Alerts -->
  <div
    v-if="
      sortedStats.some(
        (s) =>
          ['Y', 'V'].includes(s.is_avg_salary_under_500k || '') ||
          ['Y', 'V'].includes(s.is_better_eps_lower_salary || '') ||
          ['Y', 'V'].includes(s.is_eps_growth_salary_decrease || ''),
      )
    "
    class="mb-6 space-y-3"
  >
    <div v-for="stat in sortedStats" :key="stat.year">
      <template
        v-if="
          ['Y', 'V'].includes(stat.is_avg_salary_under_500k || '') ||
          ['Y', 'V'].includes(stat.is_better_eps_lower_salary || '') ||
          ['Y', 'V'].includes(stat.is_eps_growth_salary_decrease || '')
        "
      >
        <div
          class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3"
        >
          <Icon
            name="lucide:alert-triangle"
            class="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5"
          />
          <div>
            <h4 class="font-bold text-red-800 dark:text-red-300 text-sm mb-1">
              {{ stat.year }}年度 薪資警示
            </h4>
            <ul
              class="list-disc list-inside text-sm text-red-700 dark:text-red-400 space-y-1"
            >
              <li
                v-if="['Y', 'V'].includes(stat.is_avg_salary_under_500k || '')"
              >
                基層平均年薪未達 50 萬
              </li>
              <li
                v-if="
                  ['Y', 'V'].includes(stat.is_better_eps_lower_salary || '')
                "
              >
                EPS 優於同業，薪資卻低於同業水準
              </li>
              <li
                v-if="
                  ['Y', 'V'].includes(stat.is_eps_growth_salary_decrease || '')
                "
              >
                EPS 較去年成長，薪資卻不升反降
              </li>
            </ul>
          </div>
        </div>
      </template>

      <!-- Company Notes -->
      <template
        v-if="
          stat.performance_salary_relation_note ||
          stat.improvement_measures_note
        "
      >
        <div
          class="bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg p-4 text-sm mt-3"
        >
          <div
            class="flex items-center gap-2 mb-2 text-gray-900 dark:text-gray-100 font-medium"
          >
            <Icon name="lucide:info" class="w-4 h-4 text-blue-500" />
            <span>{{ stat.year }}年度 公司補充說明</span>
          </div>

          <div
            v-if="stat.performance_salary_relation_note"
            class="mb-3 last:mb-0"
          >
            <span class="block text-xs text-gray-500 dark:text-slate-400 mb-1"
              >經營績效與薪酬之關聯性與合理性：</span
            >
            <p
              class="text-gray-700 dark:text-slate-300 whitespace-pre-line leading-relaxed"
            >
              {{ stat.performance_salary_relation_note }}
            </p>
          </div>

          <div v-if="stat.improvement_measures_note">
            <span class="block text-xs text-gray-500 dark:text-slate-400 mb-1"
              >未來改善措施：</span
            >
            <p
              class="text-gray-700 dark:text-slate-300 whitespace-pre-line leading-relaxed"
            >
              {{ stat.improvement_measures_note }}
            </p>
          </div>
        </div>
      </template>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <!-- EPS Chart -->
    <div
      class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
    >
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">
        歷年 EPS 趨勢
      </h3>
      <div v-if="sortedStats.length > 0" class="h-64">
        <Chart type="bar" :data="epsData" :options="chartOptions" />
      </div>
      <div
        v-else
        class="h-64 flex items-center justify-center text-gray-400 dark:text-slate-500"
      >
        暫無 EPS 資料
      </div>
    </div>

    <!-- Salary Chart -->
    <div
      class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
    >
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">
        非主管薪資趨勢
      </h3>
      <div v-if="sortedStats.length > 0" class="h-64">
        <Line :data="salaryData" :options="chartOptions" />
      </div>
      <div
        v-else
        class="h-64 flex items-center justify-center text-gray-400 dark:text-slate-500"
      >
        暫無薪資資料
      </div>
    </div>

    <!-- Salary Growth Rate Chart -->
    <div
      v-if="hasGrowthData"
      class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
    >
      <h3
        class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
      >
        <Icon name="lucide:trending-up" class="w-5 h-5 mr-2 text-green-500" />
        薪資成長率趨勢 (YoY %)
      </h3>
      <div class="h-64">
        <Line :data="salaryGrowthData" :options="growthChartOptions" />
      </div>
    </div>

    <!-- Salary Adjustment Chart (New) -->
    <div
      class="lg:col-span-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
    >
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">
        員工酬勞分派
      </h3>
      <div v-if="sortedAdjustments.length > 0">
        <div class="h-64 mb-6">
          <Bar :data="adjustmentData" :options="chartOptions" />
        </div>

        <!-- Detailed Adjustments List -->
        <div class="mt-8 space-y-4">
          <h4 class="font-bold text-gray-900 dark:text-white mb-4">
            詳細分派資訊
          </h4>
          <div class="overflow-x-auto">
            <table
              class="w-full text-sm text-left text-gray-500 dark:text-slate-400"
            >
              <thead
                class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-slate-800 dark:text-slate-300"
              >
                <tr>
                  <th scope="col" class="px-6 py-3 whitespace-nowrap">年度</th>
                  <th
                    scope="col"
                    class="px-6 py-3 whitespace-nowrap text-right"
                  >
                    稅前淨利 (元)
                  </th>
                  <th
                    scope="col"
                    class="px-6 py-3 whitespace-nowrap text-right"
                  >
                    提撥金額 (元)
                  </th>
                  <th
                    scope="col"
                    class="px-6 py-3 whitespace-nowrap text-right"
                  >
                    實際比例 (%)
                  </th>
                  <th scope="col" class="px-6 py-3 min-w-[200px]">認定範圍</th>
                  <th scope="col" class="px-6 py-3 min-w-[200px]">差異說明</th>
                  <th scope="col" class="px-6 py-3 min-w-[150px]">備註</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="adj in sortedAdjustments"
                  :key="adj.id"
                  class="bg-white border-b dark:bg-slate-900 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800/50"
                >
                  <td
                    class="px-6 py-4 font-medium text-gray-900 dark:text-white whitespace-nowrap"
                  >
                    {{ adj.year }}
                  </td>
                  <td class="px-6 py-4 text-right">
                    {{
                      adj.pretax_net_profit
                        ? adj.pretax_net_profit.toLocaleString()
                        : "-"
                    }}
                  </td>
                  <td
                    class="px-6 py-4 text-right font-bold text-blue-600 dark:text-blue-400"
                  >
                    {{
                      adj.total_allocation_amount
                        ? adj.total_allocation_amount.toLocaleString()
                        : "-"
                    }}
                  </td>
                  <td class="px-6 py-4 text-right">
                    {{ adj.actual_allocation_ratio || "-" }}
                  </td>
                  <td class="px-6 py-4">
                    <span
                      v-if="adj.basic_employee_definition"
                      class="text-xs text-gray-600 dark:text-slate-400 block whitespace-pre-wrap leading-relaxed"
                      >{{ adj.basic_employee_definition }}</span
                    >
                    <span v-else class="text-gray-300 dark:text-slate-600"
                      >-</span
                    >
                  </td>
                  <td class="px-6 py-4">
                    <span
                      v-if="adj.difference_reason"
                      class="text-xs text-gray-600 dark:text-slate-400 block whitespace-pre-wrap leading-relaxed"
                      >{{ adj.difference_reason }}</span
                    >
                    <span v-else class="text-gray-300 dark:text-slate-600"
                      >-</span
                    >
                  </td>
                  <td class="px-6 py-4">
                    <span
                      v-if="adj.note"
                      class="text-xs text-gray-600 dark:text-slate-400 block whitespace-pre-wrap leading-relaxed"
                      >{{ adj.note }}</span
                    >
                    <span v-else class="text-gray-300 dark:text-slate-600"
                      >-</span
                    >
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div
        v-else
        class="h-48 flex flex-col items-center justify-center text-gray-400 dark:text-slate-500 border border-dashed border-gray-200 dark:border-slate-800 rounded-lg bg-gray-50/50 dark:bg-slate-900/50"
      >
        <Icon name="lucide:file-question" class="w-10 h-10 mb-2 opacity-50" />
        <p>公司尚未揭露此類資訊</p>
      </div>
    </div>
  </div>
</template>
