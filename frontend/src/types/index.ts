export type Role = "candidate" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  date_joined: string;
}

export interface JobApplication {
  id: number;
  owner: number;
  owner_email: string;
  company_name: string;
  job_title: string;
  job_description: string;
  resume_text: string;
  created_at: string;
  has_feedback: boolean;
}

export interface FeedbackResult {
  id: number;
  job_application: number;
  feedback: string;
  cover_letter_draft: string;
  generated_at: string;
}
