<script setup lang="ts">
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  type ChartOptions,
} from "chart.js";
import { Bar } from "vue-chartjs";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);

interface NonManagerSalary {
  year: number;
  avg_salary?: number | null;
  median_salary?: number | null;
  industry_avg_salary?: number | null;
}

const props = defineProps<{
  stats: NonManagerSalary[];
}>();

const isDark = useDark();

// Sort stats by year
const sortedStats = computed(() => {
  return [...props.stats].sort((a, b) => a.year - b.year);
});

// Check if we have industry data
const hasData = computed(() => {
  return sortedStats.value.some(
    (s) => s.industry_avg_salary != null && s.avg_salary != null,
  );
});

// Chart Options
const chartOptions = computed<ChartOptions<"bar">>(() => ({
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
        label: (context) => {
          const value = context.parsed.y;
          return `${context.dataset.label}: ${value?.toLocaleString() ?? "-"} 仟元`;
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
        callback: (value) => `${value}`,
      },
      title: {
        display: true,
        text: "薪資 (仟元)",
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
  },
}));

// Industry Comparison Data
const industryData = computed(() => ({
  labels: sortedStats.value.map((s) => s.year + "年"),
  datasets: [
    {
      label: "公司平均",
      data: sortedStats.value.map((s) => s.avg_salary),
      backgroundColor: "#3b82f6",
      borderRadius: 4,
    },
    {
      label: "同業平均",
      data: sortedStats.value.map((s) => s.industry_avg_salary),
      backgroundColor: "#94a3b8",
      borderRadius: 4,
    },
  ],
}));

// Calculate difference from industry
const latestDiff = computed(() => {
  const latest = sortedStats.value[sortedStats.value.length - 1];
  if (!latest?.avg_salary || !latest?.industry_avg_salary) return null;
  return latest.avg_salary - latest.industry_avg_salary;
});
</script>

<template>
  <div
    v-if="hasData"
    class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
  >
    <div class="flex items-center justify-between mb-6">
      <h3
        class="text-lg font-bold text-gray-900 dark:text-white flex items-center"
      >
        <Icon name="lucide:building-2" class="w-5 h-5 mr-2 text-blue-500" />
        同業薪資比較
      </h3>
      <span
        v-if="latestDiff !== null"
        class="text-sm font-medium px-2 py-1 rounded"
        :class="
          latestDiff >= 0
            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
        "
      >
        {{ latestDiff >= 0 ? "+" : "" }}{{ latestDiff.toLocaleString() }} 仟元
      </span>
    </div>
    <div class="h-64">
      <Bar :data="industryData" :options="chartOptions" />
    </div>
    <p class="mt-4 text-xs text-gray-500 dark:text-slate-400 text-center">
      * 同業平均來自金管會揭露資料
    </p>
  </div>
</template>
