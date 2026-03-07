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
} from "chart.js";
import { Line } from "vue-chartjs";
import type { YearlySummaryItem } from "~/types/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
);

const props = defineProps<{
  data: YearlySummaryItem[];
}>();

const isDark = useDark();

const COLORS = [
  "#ef4444",
  "#3b82f6",
  "#22c55e",
  "#eab308",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
  "#06b6d4",
  "#84cc16",
];

// Only years where at least one company has both median_salary and eps
const allYears = computed(() => {
  const years = new Set(
    props.data
      .filter(
        (d) =>
          d.non_manager_salary?.median_salary != null &&
          d.non_manager_salary?.eps != null,
      )
      .map((d) => d.year),
  );
  return Array.from(years).sort((a, b) => a - b);
});

// Unique companies
const companies = computed(() => {
  const map = new Map<string, string>();
  props.data.forEach((d) => {
    if (!map.has(d.company_code)) map.set(d.company_code, d.company_name);
  });
  return Array.from(map.entries()).map(([code, name]) => ({ code, name }));
});

const companySeriesData = computed(() =>
  companies.value.map(({ code, name }) => {
    const items = props.data
      .filter((d) => d.company_code === code)
      .sort((a, b) => a.year - b.year);

    // year → { median_salary, eps }
    const dataByYear = new Map<number, { salary: number; eps: number }>();
    items.forEach((item) => {
      const salary = item.non_manager_salary?.median_salary;
      const eps = item.non_manager_salary?.eps;
      if (salary != null && eps != null && eps !== 0)
        dataByYear.set(item.year, { salary, eps });
    });

    // Base = first year with both valid values
    const baseEntry = [...dataByYear.entries()].sort((a, b) => a[0] - b[0])[0];
    const base = baseEntry?.[1] ?? null;

    return { code, name, dataByYear, base };
  }),
);

const chartData = computed(() => ({
  labels: allYears.value.map((y) => y + "年"),
  datasets: companySeriesData.value.map(({ name, dataByYear, base }, i) => ({
    label: name.length > 10 ? name.substring(0, 10) + "…" : name,
    data: allYears.value.map((year) => {
      const d = dataByYear.get(year);
      if (!d || !base) return null;
      const salaryIndex = (d.salary / base.salary) * 100;
      const epsIndex = (d.eps / base.eps) * 100;
      return Math.round((salaryIndex - epsIndex) * 10) / 10;
    }),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: COLORS[i % COLORS.length],
    fill: false,
    tension: 0.3,
    pointRadius: 5,
    spanGaps: false,
  })),
}));

// Show if >= 2 years have valid data
const hasData = computed(() => allYears.value.length >= 2);

const chartOptions = computed<any>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "top",
      labels: { color: isDark.value ? "#e2e8f0" : "#475569" },
    },
    tooltip: {
      mode: "index",
      intersect: false,
      callbacks: {
        label: (context: any) => {
          const value = context.parsed.y;
          if (value == null) return null;
          const sign = value > 0 ? "+" : "";
          return `${context.dataset.label}: ${sign}${value.toFixed(1)}`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: isDark.value ? "#334155" : "#e2e8f0" },
      ticks: { color: isDark.value ? "#94a3b8" : "#64748b" },
    },
    y: {
      grid: { color: isDark.value ? "#334155" : "#e2e8f0" },
      ticks: {
        color: isDark.value ? "#94a3b8" : "#64748b",
        callback: (value: any) => value,
      },
      title: {
        display: true,
        text: "薪資指數 − EPS 指數",
        color: isDark.value ? "#94a3b8" : "#64748b",
      },
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
      class="text-lg font-bold text-gray-900 dark:text-white mb-2 flex items-center"
    >
      <Icon name="lucide:arrow-down-up" class="w-5 h-5 mr-2 text-red-500" />
      薪資 vs EPS 成長落差
    </h3>
    <p class="text-xs text-gray-500 dark:text-slate-400 mb-6">
      薪資指數減去 EPS 指數。0 代表薪資與 EPS 同步成長；負值越大代表 EPS 跑得越快，員工分到的比例越少。
    </p>
    <div class="h-80">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
