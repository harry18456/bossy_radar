<script setup lang="ts">
import type { SystemSyncStatus } from '~/types/api'

const api = useApi()
const config = useRuntimeConfig()
const status = ref<SystemSyncStatus | null>(null)
const isLoading = ref(true)

const fetchStatus = async () => {
  isLoading.value = true
  try {
    status.value = await api.getSystemSyncStatus()
  } catch (error) {
    console.error('Failed to fetch sync status:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchStatus()
})

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}



const aggregatedStatus = computed(() => {
  if (!status.value) return null

  const aggregate = (record: Record<string, any>) => {
    const items = Object.values(record)
    return {
      count: items.reduce((sum, item) => sum + item.count, 0),
      last_updated: items.reduce((latest, item) => {
        if (!item.last_updated) return latest
        if (!latest) return item.last_updated
        return new Date(item.last_updated) > new Date(latest) ? item.last_updated : latest
      }, null as string | null)
    }
  }

  return {
    companies: aggregate(status.value.companies),
    violations: aggregate(status.value.violations),
    mops: aggregate(status.value.mops)
  }
})
</script>

<template>
  <footer class="mt-auto border-t border-gray-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md transition-colors py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
        <!-- Brand and About -->
        <div>
          <h3 class="text-lg font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent mb-1">
            慣老闆雷達 (Bossy Radar)
          </h3>
          <p class="text-xs text-gray-500 dark:text-slate-400 max-w-md hidden md:block">
            透過公開資料透明化，我們致力於建立一個更具勞權意識的職場。
            <br>
            資料來源：政府公開資訊站與勞動部。
          </p>
        </div>

        <!-- Sync Status -->
        <div class="bg-gray-50 dark:bg-slate-800/50 rounded-xl p-3 border border-gray-100 dark:border-slate-700/50">
          <div v-if="aggregatedStatus" class="grid grid-cols-3 gap-2">
            <div class="space-y-0.5">
              <span class="block text-xs text-gray-500 dark:text-slate-400 uppercase tracking-widest font-medium">公司</span>
              <span class="block text-sm font-mono font-bold text-blue-600 dark:text-cyan-400 leading-tight">
                <CommonAnimatedNumber :value="aggregatedStatus.companies.count" />
              </span>
              <span class="block text-[10px] text-gray-500 dark:text-slate-500 truncate">
                {{ formatDate(aggregatedStatus.companies.last_updated) }}
              </span>
            </div>
            
            <div class="space-y-0.5 border-x border-gray-300 dark:border-slate-700 px-3">
              <span class="block text-xs text-gray-500 dark:text-slate-400 uppercase tracking-widest font-medium">違規</span>
              <span class="block text-sm font-mono font-bold text-blue-600 dark:text-cyan-400 leading-tight">
                <CommonAnimatedNumber :value="aggregatedStatus.violations.count" />
              </span>
              <span class="block text-[10px] text-gray-500 dark:text-slate-500 truncate">
                {{ formatDate(aggregatedStatus.violations.last_updated) }}
              </span>
            </div>

            <div class="space-y-0.5">
              <span class="block text-xs text-gray-500 dark:text-slate-400 uppercase tracking-widest font-medium">財報</span>
              <span class="block text-sm font-mono font-bold text-blue-600 dark:text-cyan-400 leading-tight">
                <CommonAnimatedNumber :value="aggregatedStatus.mops.count" />
              </span>
              <span class="block text-[10px] text-gray-500 dark:text-slate-500 truncate">
                {{ formatDate(aggregatedStatus.mops.last_updated) }}
              </span>
            </div>
          </div>
          
          <div v-else-if="isLoading" class="flex justify-center py-2">
            <Icon name="lucide:loader-2" class="w-4 h-4 text-gray-300 animate-spin" />
          </div>
        </div>
      </div>

      <div class="mt-4 pt-4 border-t border-gray-100 dark:border-slate-800 flex justify-between items-center gap-4">
        <p class="text-xs text-gray-500 dark:text-slate-400 flex items-center gap-3">
          <span>© 2026 Bossy Radar Project.</span>
          <NuxtLink to="/privacy" class="hover:text-gray-900 dark:hover:text-white transition-colors">
            隱私權政策
          </NuxtLink>
          <span class="text-gray-300 dark:text-gray-600">|</span>
          <NuxtLink to="/data-sources" class="hover:text-gray-900 dark:hover:text-white transition-colors">
            資料來源與說明
          </NuxtLink>
        </p>
        <div class="flex items-center space-x-3 text-xs text-gray-500 dark:text-slate-400">
          <span>v{{ config.public.appVersion }} ({{ config.public.dataMode }})</span>
          <span class="border-l border-gray-300 dark:border-slate-700 h-3"></span>
          <a href="https://buymeacoffee.com/harry18456" target="_blank" class="text-yellow-600 dark:text-yellow-500 hover:text-yellow-700 dark:hover:text-yellow-400 transition-colors" title="請我喝杯咖啡">
            <Icon name="simple-icons:buymeacoffee" class="w-3.5 h-3.5" />
          </a>
          <span class="border-l border-gray-300 dark:border-slate-700 h-3"></span>
          <a href="https://github.com/harry18456/bossy_radar" target="_blank" class="text-gray-500 hover:text-gray-900 dark:text-slate-400 dark:hover:text-white transition-colors">
            <Icon name="brandico:github" class="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  </footer>
</template>
