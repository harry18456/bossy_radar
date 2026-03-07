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

const allYears = computed(() => {
  const years = new Set(
    props.data
      .filter((d) => d.non_manager_salary?.eps != null && d.year >= 108)
      .map((d) => d.year),
  );
  return Array.from(years).sort((a, b) => a - b);
});

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

    const epsByYear = new Map<number, number>();
    items.forEach((item) => {
      const eps = item.non_manager_salary?.eps;
      if (eps != null && eps !== 0) epsByYear.set(item.year, eps);
    });

    const baseEps = epsByYear.get(108) ?? null;

    return { code, name, epsByYear, baseEps };
  }),
);

const chartData = computed(() => ({
  labels: allYears.value.map((y) => y + "年"),
  datasets: companySeriesData.value.map(({ name, epsByYear, baseEps }, i) => ({
    label: name.length > 10 ? name.substring(0, 10) + "…" : name,
    data: allYears.value.map((year) => {
      const eps = epsByYear.get(year);
      if (eps == null || baseEps == null) return null;
      return Math.round((eps / baseEps) * 100 * 10) / 10;
    }),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: COLORS[i % COLORS.length],
    fill: false,
    tension: 0.3,
    pointRadius: 5,
    spanGaps: false,
  })),
}));

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
          return `${context.dataset.label}: ${value.toFixed(1)}`;
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
      ticks: { color: isDark.value ? "#94a3b8" : "#64748b" },
      title: {
        display: true,
        text: "指數（各公司首年 = 100）",
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
      <Icon name="lucide:trending-up" class="w-5 h-5 mr-2 text-green-500" />
      EPS 指數化趨勢
    </h3>
    <p class="text-xs text-gray-500 dark:text-slate-400 mb-6">
      以民國 108 年為基準（= 100），呈現各公司 EPS 的相對成長幅度。
    </p>
    <div class="h-80">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
