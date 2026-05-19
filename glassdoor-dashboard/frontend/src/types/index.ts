export type DimensionKey = 'overall' | 'culture' | 'wlb' | 'salary' | 'career' | 'diversity' | 'management' | 'ceo_approval'

export const DIMENSION_LABELS: Record<DimensionKey, string> = {
  overall: 'Overall',
  culture: 'Culture & Values',
  wlb: 'Work/Life Balance',
  salary: 'Compensation',
  career: 'Career Growth',
  diversity: 'Diversity',
  management: 'Senior Mgmt',
  ceo_approval: 'CEO Approval',
}

export interface CompanyOverview {
  company: string
  rank: number
  overall: number | null
  culture: number | null
  wlb: number | null
  salary: number | null
  career: number | null
  diversity: number | null
  management: number | null
  recommend: number | null
  ceo_approval: number | null
  total_reviews: number | null
  source_mode: 'city' | 'country' | 'scan' | 'unknown'
}

export interface LocationRating {
  company: string
  baseline_location: string
  country: string | null
  overall: number | null
  culture: number | null
  wlb: number | null
  salary: number | null
  career: number | null
  diversity: number | null
  management: number | null
  recommend: number | null
  ceo_approval: number | null
  total_reviews: number | null
  source_mode: 'city' | 'country' | 'scan' | 'unknown'
}
