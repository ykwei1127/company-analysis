import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Category {
  key: string
  name: string
  companies: string[]
  location_filter: string
  weighted: boolean
}

export const CATEGORY_DEFINITIONS: Category[] = [
  {
    key: 'rd_taiwan',
    name: 'R&D in Taiwan',
    companies: ['ASUS', 'MSI', 'Trend Micro', 'Google', 'Acer'],
    location_filter: 'Taiwan',
    weighted: false
  },
  {
    key: 'brand_global',
    name: 'Global Brands',
    companies: ['ASUS', 'Acer', 'Dell Technologies', 'HP Inc.', 'Lenovo', 'MSI', 'Trend Micro', 'NVIDIA', 'Google'],
    location_filter: 'all',
    weighted: true
  },
  {
    key: 'oem_taiwan',
    name: 'Taiwan Tech OEMs',
    companies: ['ASUS', 'Quanta Computer', 'Wistron', 'Compal Electronics', 'Wiwynn', 'TSMC', 'Delta Electronics', 'Inventec', 'Pegatron', 'AU Optronics'],
    location_filter: 'Taiwan',
    weighted: false
  }
]

export const useCategoryStore = defineStore('category', () => {
  // Default to 'rd_taiwan'
  const selectedCategory = ref<string>('rd_taiwan')

  const currentCategory = computed<Category | undefined>(() =>
    CATEGORY_DEFINITIONS.find(c => c.key === selectedCategory.value)
  )

  const isWeightedCategory = computed(() =>
    currentCategory.value?.weighted ?? false
  )

  function selectCategory(key: string) {
    if (CATEGORY_DEFINITIONS.some(c => c.key === key)) {
      selectedCategory.value = key
    }
  }

  function getCategoryCompanies(key: string): string[] {
    const cat = CATEGORY_DEFINITIONS.find(c => c.key === key)
    return cat?.companies ?? []
  }

  return {
    selectedCategory,
    currentCategory,
    isWeightedCategory,
    selectCategory,
    getCategoryCompanies,
    categories: CATEGORY_DEFINITIONS
  }
})
