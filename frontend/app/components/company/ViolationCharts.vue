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
  Filler,
  type ChartOptions,
} from "chart.js";
import { Bar, Line } from "vue-chartjs";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend,
);

interface Violation {
  id: number;
  penalty_date?: string | null;
  fine_amount: number;
}

interface EnvironmentalViolation {
  id: number;
  penalty_date: string;
  fine_amount: number;
}

const props = defineProps<{
  violations: Violation[];
  environmentalViolations: EnvironmentalViolation[];
}>();

const isDark = useDark();

// Extract year from date string
const getYear = (dateStr: string | null | undefined): number | null => {
  if (!dateStr) return null;
  const year = parseInt(dateStr.substring(0, 4));
  return isNaN(year) ? null : year;
};

// Group violations by year
const yearlyData = computed(() => {
  const yearMap = new Map<
    number,
    { labor: number; env: number; laborFine: number; envFine: number }
  >();

  // Process labor violations
  props.violations.forEach((v) => {
    const year = getYear(v.penalty_date);
    if (year) {
      const existing = yearMap.get(year) || {
        labor: 0,
        env: 0,
        laborFine: 0,
        envFine: 0,
      };
      existing.labor++;
      existing.laborFine += v.fine_amount || 0;
      yearMap.set(year, existing);
    }
  });

  // Process environmental violations
  props.environmentalViolations.forEach((v) => {
    const year = getYear(v.penalty_date);
    if (year) {
      const existing = yearMap.get(year) || {
        labor: 0,
        env: 0,
        laborFine: 0,
        envFine: 0,
      };
      existing.env++;
      existing.envFine += v.fine_amount || 0;
      yearMap.set(year, existing);
    }
  });

  // Sort by year
  const sortedYears = Array.from(yearMap.keys()).sort((a, b) => a - b);

  return {
    labels: sortedYears.map((y) => `${y}年`),
    years: sortedYears,
    labor: sortedYears.map((y) => yearMap.get(y)?.labor || 0),
    env: sortedYears.map((y) => yearMap.get(y)?.env || 0),
    laborFine: sortedYears.map((y) => yearMap.get(y)?.laborFine || 0),
    envFine: sortedYears.map((y) => yearMap.get(y)?.envFine || 0),
  };
});

// Calculate cumulative fines
const cumulativeData = computed(() => {
  let laborTotal = 0;
  let envTotal = 0;

  return {
    labor: yearlyData.value.laborFine.map((f) => {
      laborTotal += f;
      return laborTotal;
    }),
    env: yearlyData.value.envFine.map((f) => {
      envTotal += f;
      return envTotal;
    }),
  };
});

// Check if we have any data to show
const hasData = computed(() => yearlyData.value.years.length > 0);

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
        stepSize: 1,
      },
      beginAtZero: true,
    },
  },
}));

const areaChartOptions = computed<ChartOptions<"line">>(() => ({
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
          return `${context.dataset.label}: ${value.toLocaleString()} 元`;
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
        callback: (value) => `${(Number(value) / 10000).toLocaleString()} 萬`,
      },
      beginAtZero: true,
    },
  },
}));

// Violation Count Chart Data
const violationCountData = computed(() => ({
  labels: yearlyData.value.labels,
  datasets: [
    {
      label: "勞動違規",
      data: yearlyData.value.labor,
      backgroundColor: "#ef4444",
      borderRadius: 4,
    },
    {
      label: "環保違規",
      data: yearlyData.value.env,
      backgroundColor: "#22c55e",
      borderRadius: 4,
    },
  ],
}));

// Cumulative Fine Chart Data
const cumulativeFineData = computed(() => ({
  labels: yearlyData.value.labels,
  datasets: [
    {
      label: "勞動罰鍰累計",
      data: cumulativeData.value.labor,
      borderColor: "#ef4444",
      backgroundColor: "rgba(239, 68, 68, 0.1)",
      fill: true,
      tension: 0.3,
    },
    {
      label: "環保罰鍰累計",
      data: cumulativeData.value.env,
      borderColor: "#22c55e",
      backgroundColor: "rgba(34, 197, 94, 0.1)",
      fill: true,
      tension: 0.3,
    },
  ],
}));

// Summary stats
const totalLaborViolations = computed(() => props.violations.length);
const totalEnvViolations = computed(() => props.environmentalViolations.length);
const totalLaborFine = computed(() =>
  props.violations.reduce((sum, v) => sum + (v.fine_amount || 0), 0),
);
const totalEnvFine = computed(() =>
  props.environmentalViolations.reduce(
    (sum, v) => sum + (v.fine_amount || 0),
    0,
  ),
);

// Stacked bar chart options
const stackedChartOptions = computed<ChartOptions<"bar">>(() => ({
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
      stacked: true,
      grid: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
    },
    y: {
      stacked: true,
      grid: {
        color: isDark.value ? "#334155" : "#e2e8f0",
      },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
        stepSize: 1,
      },
      beginAtZero: true,
    },
  },
}));

// Stacked violation data
const stackedViolationData = computed(() => ({
  labels: yearlyData.value.labels,
  datasets: [
    {
      label: "勞動違規",
      data: yearlyData.value.labor,
      backgroundColor: "#ef4444",
      borderRadius: 2,
    },
    {
      label: "環保違規",
      data: yearlyData.value.env,
      backgroundColor: "#22c55e",
      borderRadius: 2,
    },
  ],
}));
</script>

<template>
  <div v-if="hasData" class="space-y-8 mb-8">
    <!-- Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div
        class="bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-xl p-4"
      >
        <div class="text-2xl font-bold text-red-600 dark:text-red-400">
          {{ totalLaborViolations }}
        </div>
        <div class="text-sm text-red-700 dark:text-red-300">勞動違規次數</div>
      </div>
      <div
        class="bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-xl p-4"
      >
        <div class="text-2xl font-bold text-red-600 dark:text-red-400">
          {{ totalLaborFine.toLocaleString() }}
        </div>
        <div class="text-sm text-red-700 dark:text-red-300">
          勞動罰鍰總額 (元)
        </div>
      </div>
      <div
        class="bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 rounded-xl p-4"
      >
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">
          {{ totalEnvViolations }}
        </div>
        <div class="text-sm text-green-700 dark:text-green-300">
          環保違規次數
        </div>
      </div>
      <div
        class="bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 rounded-xl p-4"
      >
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">
          {{ totalEnvFine.toLocaleString() }}
        </div>
        <div class="text-sm text-green-700 dark:text-green-300">
          環保罰鍰總額 (元)
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Violation Count by Year -->
      <div
        class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
      >
        <h3
          class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
        >
          <Icon name="lucide:bar-chart-3" class="w-5 h-5 mr-2 text-blue-500" />
          違規次數年度趨勢
        </h3>
        <div class="h-64">
          <Bar :data="violationCountData" :options="chartOptions" />
        </div>
      </div>

      <!-- Cumulative Fine -->
      <div
        class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm"
      >
        <h3
          class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
        >
          <Icon
            name="lucide:trending-up"
            class="w-5 h-5 mr-2 text-orange-500"
          />
          罰鍰金額累計趨勢
        </h3>
        <div class="h-64">
          <Line :data="cumulativeFineData" :options="areaChartOptions" />
        </div>
      </div>
      <!-- Stacked Violation Comparison -->
      <div
        class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm lg:col-span-2"
      >
        <h3
          class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
        >
          <Icon name="lucide:layers" class="w-5 h-5 mr-2 text-purple-500" />
          勞動 vs 環保違規比例
        </h3>
        <div class="h-64">
          <Bar :data="stackedViolationData" :options="stackedChartOptions" />
        </div>
      </div>

      <!-- Violation Law Article Distribution -->
      <CompanyViolationDonut
        :violations="violations"
        :environmental-violations="environmentalViolations"
      />
    </div>
  </div>
</template>
