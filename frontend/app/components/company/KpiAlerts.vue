<script setup lang="ts">
interface NonManagerSalary {
  year: number;
  avg_salary?: number | null;
  median_salary?: number | null;
  eps?: number | null;
  industry_avg_salary?: number | null;
  is_avg_salary_under_500k?: string | null;
  is_better_eps_lower_salary?: string | null;
  is_eps_growth_salary_decrease?: string | null;
}

const props = defineProps<{
  stats: NonManagerSalary[];
}>();

// Get latest year stats
const latestStats = computed(() => {
  if (props.stats.length === 0) return null;
  return [...props.stats].sort((a, b) => b.year - a.year)[0];
});

// Warnings check
const hasWarnings = computed(() => {
  if (!latestStats.value) return false;
  const s = latestStats.value;
  return (
    ["Y", "V"].includes(s.is_avg_salary_under_500k || "") ||
    ["Y", "V"].includes(s.is_better_eps_lower_salary || "") ||
    ["Y", "V"].includes(s.is_eps_growth_salary_decrease || "")
  );
});
</script>

<template>
  <div
    v-if="latestStats"
    class="grid grid-cols-3 gap-4 mb-8"
  >
    <!-- Latest Year Salary -->
    <div
      class="bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4"
    >
      <div class="flex items-center justify-between mb-2">
        <Icon
          name="lucide:wallet"
          class="w-5 h-5 text-green-600 dark:text-green-400"
        />
        <span class="text-xs text-green-600 dark:text-green-400"
          >{{ latestStats?.year }}年</span
        >
      </div>
      <div class="text-2xl font-bold text-green-700 dark:text-green-300">
        {{
          latestStats?.avg_salary
            ? latestStats.avg_salary.toLocaleString()
            : "-"
        }}
      </div>
      <div class="text-xs text-green-600 dark:text-green-400">
        平均薪資 (仟元)
      </div>
    </div>

    <!-- Median Salary -->
    <div
      class="bg-gradient-to-br from-yellow-50 to-amber-100 dark:from-yellow-900/30 dark:to-amber-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4"
    >
      <div class="flex items-center justify-between mb-2">
        <Icon
          name="lucide:bar-chart-2"
          class="w-5 h-5 text-yellow-600 dark:text-yellow-400"
        />
        <span class="text-xs text-yellow-600 dark:text-yellow-400"
          >{{ latestStats?.year }}年</span
        >
      </div>
      <div class="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
        {{
          latestStats?.median_salary
            ? latestStats.median_salary.toLocaleString()
            : "-"
        }}
      </div>
      <div class="text-xs text-yellow-600 dark:text-yellow-400">
        中位數薪資 (仟元)
      </div>
    </div>

    <!-- EPS -->
    <div
      class="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4"
    >
      <div class="flex items-center justify-between mb-2">
        <Icon
          name="lucide:trending-up"
          class="w-5 h-5 text-blue-600 dark:text-blue-400"
        />
        <span class="text-xs text-blue-600 dark:text-blue-400"
          >{{ latestStats?.year }}年</span
        >
      </div>
      <div class="text-2xl font-bold text-blue-700 dark:text-blue-300">
        {{ latestStats?.eps ?? "-" }}
      </div>
      <div class="text-xs text-blue-600 dark:text-blue-400">每股盈餘 (EPS)</div>
    </div>



    <!-- Warning Alert -->
    <div
      v-if="hasWarnings"
      class="col-span-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4"
    >
      <div class="flex items-center gap-3">
        <Icon
          name="lucide:alert-circle"
          class="w-6 h-6 text-red-600 dark:text-red-400 shrink-0"
        />
        <div>
          <h4 class="font-bold text-red-800 dark:text-red-300 text-sm">
            {{ latestStats?.year }}年度 薪資警示
          </h4>
          <ul
            class="list-disc list-inside text-sm text-red-700 dark:text-red-400 mt-1 space-y-0.5"
          >
            <li
              v-if="
                ['Y', 'V'].includes(latestStats?.is_avg_salary_under_500k || '')
              "
            >
              基層平均年薪未達 50 萬
            </li>
            <li
              v-if="
                ['Y', 'V'].includes(
                  latestStats?.is_better_eps_lower_salary || '',
                )
              "
            >
              EPS 優於同業，薪資卻低於同業水準
            </li>
            <li
              v-if="
                ['Y', 'V'].includes(
                  latestStats?.is_eps_growth_salary_decrease || '',
                )
              "
            >
              EPS 較去年成長，薪資卻不升反降
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
