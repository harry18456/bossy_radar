<template>
  <div class="fixed inset-0 overflow-hidden pointer-events-none z-0">
    <!-- Grid Pattern -->
    <div class="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] dark:bg-[linear-gradient(to_right,#ffffff0a_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0a_1px,transparent_1px)]"></div>
    
    <!-- Gradient Orbs -->
    <div class="absolute -top-[40%] -left-[20%] w-[70%] h-[70%] rounded-full bg-blue-400/30 dark:bg-blue-600/30 blur-[120px] animate-blob-1"></div>
    <div class="absolute top-[20%] -right-[20%] w-[70%] h-[70%] rounded-full bg-cyan-400/30 dark:bg-cyan-600/30 blur-[120px] animate-blob-2 animation-delay-2000"></div>
    <div class="absolute -bottom-[40%] left-[20%] w-[70%] h-[70%] rounded-full bg-purple-400/30 dark:bg-purple-600/30 blur-[120px] animate-blob-3 animation-delay-4000"></div>
  </div>
</template>

<style scoped>
@keyframes blob-1 {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0px, 0px) scale(1); }
}

@keyframes blob-2 {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(-30px, 40px) scale(1.1); }
  66% { transform: translate(20px, -30px) scale(0.95); }
  100% { transform: translate(0px, 0px) scale(1); }
}

@keyframes blob-3 {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.05); }
  66% { transform: translate(-30px, 40px) scale(0.9); }
  100% { transform: translate(0px, 0px) scale(1); }
}

.animate-blob-1 {
  animation: blob-1 10s infinite;
  will-change: transform;
}
.animate-blob-2 {
  animation: blob-2 10s infinite;
  will-change: transform;
}
.animate-blob-3 {
  animation: blob-3 10s infinite;
  will-change: transform;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}
</style>
