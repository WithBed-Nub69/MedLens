import { createClient } from '@supabase/supabase-js'

const supabaseUrl =
  import.meta.env.VITE_SUPABASE_URL ||
  'https://qufdpqjopdowaiopwvve.supabase.co'
const supabaseAnonKey =
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1ZmRwcWpvcGRvd2Fpb3B3dnZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1Nzk4MjUsImV4cCI6MjEwNDE1NTgyNX0.ezFiJnUflTnXugNnyAul9boM5evOUpfrWUeRbIa9fcE'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

