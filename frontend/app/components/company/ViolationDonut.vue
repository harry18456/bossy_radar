<script setup lang="ts">
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement } from "chart.js";
import { Doughnut } from "vue-chartjs";

ChartJS.register(ArcElement, Title, Tooltip, Legend);

interface Violation {
  id: number;
  fine_amount: number;
  law_article?: string | null;
}

interface EnvironmentalViolation {
  id: number;
  fine_amount: number;
  law_article?: string | null;
}

const props = defineProps<{
  violations: Violation[];
  environmentalViolations: EnvironmentalViolation[];
}>();

const isDark = useDark();

// Parse law article to get the main article number
const parseArticle = (article: string | null | undefined): string => {
  if (!article) return "其他";
  // Extract main article reference (e.g., "第30條" -> "第30條")
  const match = article.match(/第\d+條/);
  return match
    ? match[0]
    : article.substring(0, 15) + (article.length > 15 ? "..." : "");
};

// Aggregate violations by law article
const articleStats = computed(() => {
  const stats: Record<string, { count: number; fine: number }> = {};

  // Process labor violations
  for (const v of props.violations) {
    const article = parseArticle(v.law_article);
    if (!stats[article]) {
      stats[article] = { count: 0, fine: 0 };
    }
    stats[article].count++;
    stats[article].fine += v.fine_amount || 0;
  }

  // Process environmental violations
  for (const v of props.environmentalViolations) {
    const article = parseArticle(v.law_article);
    if (!stats[article]) {
      stats[article] = { count: 0, fine: 0 };
    }
    stats[article].count++;
    stats[article].fine += v.fine_amount || 0;
  }

  // Sort by count and get top 8
  return Object.entries(stats)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 8);
});

const hasData = computed(() => articleStats.value.length > 0);

// Colors for donut
const colors = [
  "#ef4444",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#14b8a6",
  "#3b82f6",
  "#8b5cf6",
  "#ec4899",
];

// Donut chart data
const donutData = computed(() => ({
  labels: articleStats.value.map(([article]) => article),
  datasets: [
    {
      data: articleStats.value.map(([, stats]) => stats.count),
      backgroundColor: colors.slice(0, articleStats.value.length),
      borderWidth: 2,
      borderColor: isDark.value ? "#0f172a" : "#ffffff",
    },
  ],
}));

// Donut options
const donutOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: "60%",
  plugins: {
    legend: {
      position: "right" as const,
      labels: {
        color: isDark.value ? "#e2e8f0" : "#475569",
        usePointStyle: true,
        padding: 12,
        font: {
          size: 11,
        },
      },
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const stats = articleStats.value[context.dataIndex];
          return [
            `次數: ${stats[1].count}`,
            `罰鍰: ${stats[1].fine.toLocaleString()} 元`,
          ];
        },
      },
    },
  },
}));
</script>

<template>
  <div
    v-if="hasData"
    class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6 shadow-sm lg:col-span-2"
  >
    <h3
      class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center"
    >
      <Icon name="lucide:pie-chart" class="w-5 h-5 mr-2 text-red-500" />
      違規法條分佈
    </h3>
    <div class="h-72">
      <Doughnut :data="donutData" :options="donutOptions" />
    </div>
    <p class="mt-4 text-xs text-gray-500 dark:text-slate-400 text-center">
      * 顯示違規次數最多的前8項法條
    </p>
  </div>
</template>
