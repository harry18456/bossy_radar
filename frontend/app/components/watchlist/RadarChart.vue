<script setup lang="ts">
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  Filler,
  RadialLinearScale,
} from "chart.js";
import { Radar } from "vue-chartjs";

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend,
);

interface ComparisonItem {
  company_code: string;
  company_name: string;
  violations_total_count?: number | null;
  env_violations_total_count?: number | null;
  non_manager_salary?: {
    avg_salary?: number | null;
    median_salary?: number | null;
    eps?: number | null;
    employee_count?: number | null;
  } | null;
}

const props = defineProps<{
  data: ComparisonItem[];
  year: number | null;
}>();

const isDark = useDark();

// Check if we have enough data
const hasData = computed(() => props.data.length >= 2);

// Normalize values to 0-100 scale for radar
const normalize = (values: number[], invert = false) => {
  const max = Math.max(...values);
  if (max === 0) return values.map(() => 0);
  return values.map((v) => {
    const normalized = (v / max) * 100;
    return invert ? 100 - normalized : normalized;
  });
};

// Colors for each company
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

// Radar data
const radarData = computed(() => {
  const salaries = props.data.map(
    (item) => item.non_manager_salary?.avg_salary || 0,
  );
  const medians = props.data.map(
    (item) => item.non_manager_salary?.median_salary || 0,
  );
  const eps = props.data.map((item) => item.non_manager_salary?.eps || 0);
  const violations = props.data.map(
    (item) =>
      (item.violations_total_count || 0) +
      (item.env_violations_total_count || 0),
  );

  // Normalize all values
  const normSalary = normalize(salaries);
  const normMedian = normalize(medians);
  const normEps = normalize(eps);
  const normViolations = normalize(violations, true); // Invert - less violations is better

  return {
    labels: ["平均薪資", "中位數薪資", "EPS", "守法程度"],
    datasets: props.data.slice(0, 6).map((item, i) => ({
      label:
        item.company_name.length > 6
          ? item.company_name.substring(0, 6) + "..."
          : item.company_name,
      data: [normSalary[i], normMedian[i], normEps[i], normViolations[i]],
      fill: true,
      backgroundColor: `${colors[i % colors.length]}20`,
      borderColor: colors[i % colors.length],
      pointBackgroundColor: colors[i % colors.length],
      pointBorderColor: "#fff",
      pointHoverBackgroundColor: "#fff",
      pointHoverBorderColor: colors[i % colors.length],
    })),
  };
});

// Radar options
const radarOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "bottom" as const,
      labels: {
        color: isDark.value ? "#e2e8f0" : "#475569",
        usePointStyle: true,
      },
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          return `${context.dataset.label}: ${context.parsed.r.toFixed(0)}分`;
        },
      },
    },
  },
  scales: {
    r: {
      grid: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      pointLabels: {
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
      angleLines: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      ticks: {
        backdropColor: "transparent",
        color: isDark.value ? "#64748b" : "#94a3b8",
      },
      min: 0,
      max: 100,
    },
  },
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
      <Icon name="lucide:radar" class="w-5 h-5 mr-2 text-purple-500" />
      多維度雷達圖 ({{ year }}年)
    </h3>
    <div class="h-80">
      <Radar :data="radarData" :options="radarOptions" />
    </div>
    <p class="mt-4 text-xs text-gray-500 dark:text-slate-400 text-center">
      * 數值已正規化為 0-100
      分，「守法程度」為違規次數反向計算（違規越少分數越高）
    </p>
  </div>
</template>
