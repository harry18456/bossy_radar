export const useDark = () => {
    const colorMode = useColorMode()
    return computed(() => colorMode.value === 'dark')
}
