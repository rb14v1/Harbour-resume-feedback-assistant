import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import type { FeedbackResult, JobApplication } from "../../types";
import { fetchApplication, fetchFeedback, generateFeedback } from "./api";

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>();
  const applicationId = Number(id);

  const [application, setApplication] = useState<JobApplication | null>(null);
  const [feedback, setFeedback] = useState<FeedbackResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [app, fb] = await Promise.all([
        fetchApplication(applicationId),
        fetchFeedback(applicationId),
      ]);
      setApplication(app);
      setFeedback(fb);
      setError(null);
    } catch {
      setError("Failed to load application.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applicationId]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const fb = await generateFeedback(applicationId);
      setFeedback(fb);
    } catch {
      setError("Failed to generate feedback.");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error || !application) return <p style={{ color: "red" }}>{error ?? "Not found."}</p>;

  return (
    <div>
      <h2>
        {application.job_title} @ {application.company_name}
      </h2>

      <h3>Job description</h3>
      <pre style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: "0.5rem" }}>
        {application.job_description}
      </pre>

      <h3>Resume text</h3>
      <pre style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: "0.5rem" }}>
        {application.resume_text}
      </pre>

      <button onClick={handleGenerate} disabled={generating}>
        {generating ? "Generating..." : feedback ? "Regenerate feedback" : "Generate feedback"}
      </button>

      {feedback && (
        <>
          <h3>Feedback</h3>
          <pre style={{ whiteSpace: "pre-wrap", background: "#eef", padding: "0.5rem" }}>
            {feedback.feedback}
          </pre>

          <h3>Cover letter draft</h3>
          <pre style={{ whiteSpace: "pre-wrap", background: "#eef", padding: "0.5rem" }}>
            {feedback.cover_letter_draft}
          </pre>
        </>
      )}
      {!feedback && <p>No feedback generated yet.</p>}
    </div>
  );
}
