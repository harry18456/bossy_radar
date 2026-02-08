<script setup lang="ts">
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LinearScale,
  type ChartOptions,
} from "chart.js";
import { Scatter } from "vue-chartjs";

ChartJS.register(LinearScale, PointElement, Title, Tooltip, Legend);

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

// Check if we have enough data to show scatter
const hasData = computed(() => {
  return (
    props.data.filter(
      (item) =>
        item.non_manager_salary?.median_salary &&
        item.non_manager_salary?.eps != null,
    ).length >= 2
  );
});

// Scatter chart options
const scatterOptions = computed<ChartOptions<"scatter">>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const item = filteredData.value[context.dataIndex];
          return [
            item?.company_name || "",
            `EPS: ${context.parsed.x}`,
            `薪資: ${context.parsed.y?.toLocaleString() ?? "-"} 仟元`,
          ];
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
      title: {
        display: true,
        text: "EPS (每股盈餘)",
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
        text: "中位數薪資 (仟元)",
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
  },
}));

// Filtered data with valid values (used for both scatter and tooltip)
const filteredData = computed(() =>
  props.data.filter(
    (item) =>
      item.non_manager_salary?.median_salary &&
      item.non_manager_salary?.eps != null,
  ),
);

// Scatter data - EPS vs Salary
const scatterData = computed(() => ({
  datasets: [
    {
      label: "公司",
      data: filteredData.value.map((item) => ({
        x: item.non_manager_salary?.eps || 0,
        y: item.non_manager_salary?.median_salary || 0,
      })),
      backgroundColor: filteredData.value.map((_, i) => {
        const colors = [
          "#ef4444",
          "#3b82f6",
          "#22c55e",
          "#eab308",
          "#8b5cf6",
          "#ec4899",
          "#14b8a6",
          "#f97316",
        ];
        return colors[i % colors.length];
      }),
      pointRadius: 10,
      pointHoverRadius: 14,
    },
  ],
}));
</script>

<template>
  <div
    v-if="hasData"
    class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm mb-8"
  >
    <h3
      class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
    >
      <Icon name="lucide:scatter-chart" class="w-5 h-5 mr-2 text-blue-500" />
      薪資 vs EPS 散佈圖 ({{ year }}年)
    </h3>
    <div class="h-80">
      <Scatter :data="scatterData" :options="scatterOptions" />
    </div>
    <p class="mt-4 text-xs text-gray-500 dark:text-slate-400 text-center">
      * 圓點顏色代表不同公司，X軸為EPS、Y軸為中位數薪資
    </p>
  </div>
</template>
