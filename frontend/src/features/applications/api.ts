import { apiClient } from "../../api/client";
import type { FeedbackResult, JobApplication } from "../../types";

export async function fetchApplications(): Promise<JobApplication[]> {
  const { data } = await apiClient.get<JobApplication[]>("/applications/");
  return data;
}

export async function fetchApplication(id: number): Promise<JobApplication> {
  const { data } = await apiClient.get<JobApplication>(`/applications/${id}/`);
  return data;
}

export async function createApplication(payload: {
  company_name: string;
  job_title: string;
  job_description: string;
  resume_text: string;
}): Promise<JobApplication> {
  const { data } = await apiClient.post<JobApplication>("/applications/", payload);
  return data;
}

export async function deleteApplication(id: number): Promise<void> {
  await apiClient.delete(`/applications/${id}/`);
}

export async function generateFeedback(id: number): Promise<FeedbackResult> {
  const { data } = await apiClient.post<FeedbackResult>(`/applications/${id}/generate-feedback/`);
  return data;
}

export async function fetchFeedback(id: number): Promise<FeedbackResult | null> {
  try {
    const { data } = await apiClient.get<FeedbackResult>(`/applications/${id}/feedback/`);
    return data;
  } catch (err: any) {
    if (err?.response?.status === 404) {
      return null;
    }
    throw err;
  }
}
