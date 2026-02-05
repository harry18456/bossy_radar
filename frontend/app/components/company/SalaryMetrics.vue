<script setup lang="ts">
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler,
  type ChartOptions,
} from "chart.js";
import { Line } from "vue-chartjs";

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Filler,
  Title,
  Tooltip,
  Legend,
);

interface NonManagerSalary {
  year: number;
  avg_salary?: number | null;
  median_salary?: number | null;
  employee_count?: number | null;
}

const props = defineProps<{
  stats: NonManagerSalary[];
}>();

const isDark = useDark();

// Sort stats by year
const sortedStats = computed(() => {
  return [...props.stats].sort((a, b) => a.year - b.year);
});

// Check if we have disparity data
const hasDisparityData = computed(() => {
  return sortedStats.value.some(
    (s) => s.avg_salary != null && s.median_salary != null,
  );
});

// Check if we have employee count data
const hasEmployeeData = computed(() => {
  return sortedStats.value.some(
    (s) => s.employee_count != null && s.employee_count > 0,
  );
});

// Salary Disparity Data
const disparityData = computed(() => ({
  labels: sortedStats.value.map((s) => s.year + "年"),
  datasets: [
    {
      label: "薪資差距 (平均 - 中位數)",
      data: sortedStats.value.map((s) =>
        s.avg_salary != null && s.median_salary != null
          ? s.avg_salary - s.median_salary
          : null,
      ),
      borderColor: "#f59e0b",
      backgroundColor: "rgba(245, 158, 11, 0.1)",
      fill: true,
      tension: 0.3,
    },
  ],
}));

// Employee Count Data
const employeeData = computed(() => ({
  labels: sortedStats.value.map((s) => s.year + "年"),
  datasets: [
    {
      label: "員工人數",
      data: sortedStats.value.map((s) => s.employee_count),
      borderColor: "#6366f1",
      backgroundColor: "rgba(99, 102, 241, 0.1)",
      fill: true,
      tension: 0.3,
    },
  ],
}));

// Chart Options
const disparityOptions = computed<ChartOptions<"line">>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const value = context.parsed.y;
          const status = value > 0 ? "偏態分佈" : "正常";
          return `差距: ${value?.toLocaleString() ?? "-"} 仟元 (${status})`;
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
        callback: (value) => `${value} 仟元`,
      },
    },
  },
}));

const employeeOptions = computed<ChartOptions<"line">>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          return `員工人數: ${context.parsed.y?.toLocaleString() ?? "-"} 人`;
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
      },
      title: {
        display: true,
        text: "人數",
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
  },
}));

// Latest disparity value
const latestDisparity = computed(() => {
  const latest = sortedStats.value[sortedStats.value.length - 1];
  if (!latest?.avg_salary || !latest?.median_salary) return null;
  return latest.avg_salary - latest.median_salary;
});
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <!-- Salary Disparity Chart -->
    <div
      v-if="hasDisparityData"
      class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
    >
      <div class="flex items-center justify-between mb-6">
        <h3
          class="text-lg font-bold text-gray-900 dark:text-white flex items-center"
        >
          <Icon name="lucide:scale-3d" class="w-5 h-5 mr-2 text-amber-500" />
          薪資差距趨勢
        </h3>
        <span
          v-if="latestDisparity !== null"
          class="text-xs font-medium px-2 py-1 rounded"
          :class="
            latestDisparity > 100
              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
              : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
          "
        >
          {{ latestDisparity > 100 ? "偏態" : "正常" }}
        </span>
      </div>
      <div class="h-48">
        <Line :data="disparityData" :options="disparityOptions" />
      </div>
      <p class="mt-3 text-xs text-gray-500 dark:text-slate-400 text-center">
        * 差距 = 平均薪資 - 中位數薪資，差距越大表示薪資分佈越偏態
      </p>
    </div>

    <!-- Employee Count Trend -->
    <div
      v-if="hasEmployeeData"
      class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
    >
      <h3
        class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
      >
        <Icon name="lucide:users" class="w-5 h-5 mr-2 text-indigo-500" />
        員工人數變化
      </h3>
      <div class="h-48">
        <Line :data="employeeData" :options="employeeOptions" />
      </div>
    </div>
  </div>
</template>
