/**
 * Format ISO date string to YYYY/MM/DD
 * @param dateString ISO date string
 * @returns Formatted date string or original string if invalid
 */
export const formatDate = (dateString?: string | null): string => {
  if (!dateString) return '-'
  
  // Handle ROC date format like "080/01/01" or "0800101"
  const rocMatch = dateString.match(/^(\d{2,3})[\/-]?(\d{2})[\/-]?(\d{2})$/)
  if (rocMatch && rocMatch[1] && rocMatch[2] && rocMatch[3]) {
    const year = parseInt(rocMatch[1]) + 1911
    const month = rocMatch[2]
    const day = rocMatch[3]
    return `${year}/${month}/${day}`
  }

  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return dateString
    
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  } catch (e) {
    return dateString
  }
}

/**
 * Format ROC year (e.g. 112) to Western year (e.g. 2023)
 * @param rocYear ROC year number
 * @returns Western year number
 */
export const rocToWestern = (rocYear?: number | null): number | string => {
  if (!rocYear) return '-'
  return rocYear + 1911
}

/**
 * Format currency number
 * @param amount Number to format
 * @returns Formatted string with commas (e.g. "1,000")
 */
export const formatCurrency = (amount?: number | null): string => {
  if (amount === undefined || amount === null) return '-'
  return new Intl.NumberFormat('zh-TW').format(amount)
}
