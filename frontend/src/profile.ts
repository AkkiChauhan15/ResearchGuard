import { supabase } from './auth'

export const researchRoles = [
  'Undergraduate',
  'Master’s student',
  'PhD researcher',
  'Postdoctoral researcher',
  'Faculty',
  'Research staff',
  'Other',
] as const

export type ResearchRole = typeof researchRoles[number]

export interface ResearcherProfile {
  full_name: string
  research_role: ResearchRole | ''
  research_field: string
  institution: string
}

export const emptyProfile: ResearcherProfile = {
  full_name: '',
  research_role: '',
  research_field: '',
  institution: '',
}

function profileUnavailable(): Error {
  return new Error('Profile details are unavailable until the profile migration is applied.')
}

export async function loadProfile(): Promise<ResearcherProfile | null> {
  if (!supabase) throw profileUnavailable()
  const { data, error } = await supabase
    .from('researcher_profiles')
    .select('full_name,research_role,research_field,institution')
    .maybeSingle()
  if (error) throw profileUnavailable()
  if (!data) return null
  return {
    full_name: typeof data.full_name === 'string' ? data.full_name : '',
    research_role: researchRoles.includes(data.research_role as ResearchRole)
      ? data.research_role as ResearchRole
      : '',
    research_field: typeof data.research_field === 'string' ? data.research_field : '',
    institution: typeof data.institution === 'string' ? data.institution : '',
  }
}

export async function saveProfile(profile: ResearcherProfile): Promise<void> {
  if (!supabase) throw profileUnavailable()
  const optional = (value: string) => value.trim() || null
  const { error } = await supabase
    .from('researcher_profiles')
    .upsert({
      full_name: optional(profile.full_name),
      research_role: optional(profile.research_role),
      research_field: optional(profile.research_field),
      institution: optional(profile.institution),
    }, { onConflict: 'user_id' })
  if (error) throw profileUnavailable()
}
