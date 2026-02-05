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

interface ComparisonItem {
  company_code: string;
  company_name: string;
  non_manager_salary?: {
    avg_salary?: number | null;
    median_salary?: number | null;
    eps?: number | null;
  } | null;
}

const props = defineProps<{
  data: ComparisonItem[];
  year: number | null;
}>();

const isDark = useDark();

// Check if we have salary data to show
const hasData = computed(() => {
  return props.data.some(
    (item) =>
      item.non_manager_salary?.avg_salary ||
      item.non_manager_salary?.median_salary,
  );
});

// Chart Options
const chartOptions = computed<ChartOptions<"bar">>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: "y" as const,
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
          const value = context.parsed.x;
          return `${context.dataset.label}: ${value.toLocaleString()} 仟元`;
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
        callback: (value) => `${value}`,
      },
      title: {
        display: true,
        text: "薪資 (仟元)",
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
    y: {
      grid: {
        display: false,
      },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
  },
}));

// Salary Comparison Chart Data
const salaryComparisonData = computed(() => ({
  labels: props.data.map((item) =>
    item.company_name.length > 8
      ? item.company_name.substring(0, 8) + "..."
      : item.company_name,
  ),
  datasets: [
    {
      label: "平均薪資",
      data: props.data.map((item) => item.non_manager_salary?.avg_salary || 0),
      backgroundColor: "#22c55e",
      borderRadius: 4,
    },
    {
      label: "中位數薪資",
      data: props.data.map(
        (item) => item.non_manager_salary?.median_salary || 0,
      ),
      backgroundColor: "#eab308",
      borderRadius: 4,
    },
  ],
}));

// Calculate chart height based on number of companies
const chartHeight = computed(() => {
  const baseHeight = 60;
  const perItemHeight = 50;
  return Math.max(200, baseHeight + props.data.length * perItemHeight);
});
</script>

<template>
  <div
    v-if="hasData"
    class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm mb-8"
  >
    <h3
      class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
    >
      <Icon
        name="lucide:bar-chart-horizontal"
        class="w-5 h-5 mr-2 text-green-500"
      />
      非主管薪資比較 ({{ year }}年)
    </h3>
    <div :style="{ height: chartHeight + 'px' }">
      <Bar :data="salaryComparisonData" :options="chartOptions" />
    </div>
    <p class="mt-4 text-xs text-gray-500 dark:text-slate-400 text-center">
      * 薪資單位：仟元（新台幣）
    </p>
  </div>
</template>
