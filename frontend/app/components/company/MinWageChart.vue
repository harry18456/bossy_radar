<script setup lang="ts">
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  LinearScale,
  CategoryScale,
  LineController,
} from "chart.js";
import { Line } from "vue-chartjs";

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  LineController,
  PointElement,
  Title,
  Tooltip,
  Legend,
);

const props = defineProps<{
  stats: any[]; // NonManagerSalary[]
}>();

// 最低工資月薪歷史對照表（勞動部公告）
// 資料來源：https://www.mol.gov.tw/topic/3067/14530/
// 更新時請同步修改此常數表
const MIN_WAGE_MONTHLY: Record<number, number> = {
  106: 21009,
  107: 22000,
  108: 23100,
  109: 23800,
  110: 24000,
  111: 25250,
  112: 26400,
  113: 27470,
  114: 28590,
  115: 29500,
};

const sortedStats = computed(() =>
  [...props.stats].sort((a, b) => a.year - b.year),
);

// 有效年份：公司有 median_salary 且最低工資常數表也有對應年份
const validYears = computed(() =>
  sortedStats.value
    .filter((s) => s.median_salary != null && s.year in MIN_WAGE_MONTHLY)
    .map((s) => s.year),
);

// 至少需要 2 年才能計算成長率
const hasMinWageData = computed(() => validYears.value.length >= 2);

// 各年 median_salary 查找表
const yearToMedian = computed(() =>
  Object.fromEntries(
    sortedStats.value
      .filter((s) => s.median_salary != null)
      .map((s) => [s.year, s.median_salary as number]),
  ),
);

// 最低工資 YoY 成長率（第一個有效年份為 null）
const minWageGrowthRates = computed(() =>
  validYears.value.map((year, i) => {
    if (i === 0) return null;
    const prevYear = validYears.value[i - 1];
    const prevWage = MIN_WAGE_MONTHLY[prevYear];
    const currWage = MIN_WAGE_MONTHLY[year];
    if (!prevWage || !currWage) return null;
    return ((currWage - prevWage) / prevWage) * 100;
  }),
);

// 非主管中位數薪資 YoY 成長率（第一個有效年份為 null）
const medianGrowthRates = computed(() =>
  validYears.value.map((year, i) => {
    if (i === 0) return null;
    const prevYear = validYears.value[i - 1];
    const prevSalary = yearToMedian.value[prevYear];
    const currSalary = yearToMedian.value[year];
    if (!prevSalary || !currSalary) return null;
    return ((currSalary - prevSalary) / prevSalary) * 100;
  }),
);

// 低於最低工資調漲率的年份（兩者皆有值才比較）
const yearsBelowMinWage = computed(() =>
  validYears.value
    .map((year, i) => {
      const medianRate = medianGrowthRates.value[i];
      const minWageRate = minWageGrowthRates.value[i];
      if (medianRate == null || minWageRate == null) return null;
      return medianRate < minWageRate
        ? { year, medianRate, minWageRate }
        : null;
    })
    .filter((v): v is { year: number; medianRate: number; minWageRate: number } => v !== null),
);

// 中位數折線各點顏色：低於最低工資調漲率的點標紅
const medianPointColors = computed(() =>
  validYears.value.map((year, i) => {
    const medianRate = medianGrowthRates.value[i];
    const minWageRate = minWageGrowthRates.value[i];
    if (medianRate == null || minWageRate == null) return "#eab308";
    return medianRate < minWageRate ? "#ef4444" : "#eab308";
  }),
);

const chartData = computed(() => ({
  labels: validYears.value.map((y) => y + "年"),
  datasets: [
    {
      label: "非主管中位數薪資成長率 (%)",
      data: medianGrowthRates.value,
      borderColor: "#eab308",
      backgroundColor: "rgba(234, 179, 8, 0.1)",
      pointBackgroundColor: medianPointColors.value,
      pointBorderColor: medianPointColors.value,
      fill: true,
      tension: 0.3,
      pointRadius: 6,
      spanGaps: false,
    },
    {
      label: "最低工資調漲率 (%)",
      data: minWageGrowthRates.value,
      borderColor: "#ef4444",
      backgroundColor: "rgba(239, 68, 68, 0.08)",
      borderDash: [6, 4],
      fill: true,
      tension: 0.3,
      pointRadius: 5,
      spanGaps: false,
    },
  ],
}));

const isDark = useDark();

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
      callbacks: {
        label: (context: any) => {
          const value = context.parsed.y;
          if (value == null) return `${context.dataset.label}: -`;
          return `${context.dataset.label}: ${value.toFixed(2)}%`;
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
</script>

<template>
  <div
    v-if="hasMinWageData"
    class="lg:col-span-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
  >
    <h3
      class="text-lg font-bold text-gray-900 dark:text-white mb-2 flex items-center"
    >
      <Icon name="lucide:landmark" class="w-5 h-5 mr-2 text-red-500" />
      薪資成長率 vs 最低工資調漲率
    </h3>
    <p class="text-xs text-gray-500 dark:text-slate-400 mb-6">
      比較公司非主管中位數薪資的年增率（%）與政府公告最低工資調漲率。若公司線長期低於紅色基準線，代表薪資漲幅跑輸基本工資。
    </p>
    <div class="h-64">
      <Line :data="chartData" :options="chartOptions" />
    </div>

    <!-- 低於最低工資調漲率警示 -->
    <div
      v-if="yearsBelowMinWage.length > 0"
      class="mt-4 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/20"
    >
      <Icon
        name="lucide:alert-triangle"
        class="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400"
      />
      <div class="text-sm text-amber-800 dark:text-amber-300">
        <span class="font-semibold">薪資漲幅低於最低工資調漲率：</span>
        <span>
          以下
          {{ yearsBelowMinWage.length }} 個年度，公司中位數薪資成長率未達政府公告最低工資調漲幅度——
        </span>
        <span
          v-for="(item, i) in yearsBelowMinWage"
          :key="item.year"
        >
          <span class="font-medium">{{ item.year }}年</span>（{{ item.medianRate.toFixed(1) }}% vs {{ item.minWageRate.toFixed(1) }}%）<span v-if="i < yearsBelowMinWage.length - 1">、</span>
        </span>
      </div>
    </div>
  </div>
</template>
