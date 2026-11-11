import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { JobApplication } from "../../types";
import { createApplication, deleteApplication, fetchApplications } from "./api";

export default function ApplicationList() {
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeText, setResumeText] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchApplications();
      setApplications(data);
      setError(null);
    } catch {
      setError("Failed to load applications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await createApplication({
        company_name: companyName,
        job_title: jobTitle,
        job_description: jobDescription,
        resume_text: resumeText,
      });
      setCompanyName("");
      setJobTitle("");
      setJobDescription("");
      setResumeText("");
      await load();
    } catch (err: any) {
      const data = err?.response?.data;
      const message =
        typeof data === "string"
          ? data
          : data
          ? Object.values(data).flat().join(" ")
          : "Could not create application.";
      setFormError(message);
    }
  };

  const handleDelete = async (id: number) => {
    await deleteApplication(id);
    await load();
  };

  return (
    <div>
      <h2>My Job Applications</h2>

      <form onSubmit={handleSubmit} style={{ marginBottom: "1.5rem" }}>
        <h3>New Application</h3>
        {formError && <p style={{ color: "red" }}>{formError}</p>}
        <div>
          <label>
            Company:{" "}
            <input value={companyName} onChange={(e) => setCompanyName(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>
            Job title:{" "}
            <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>
            Job description:
            <br />
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={5}
              cols={60}
              required
            />
          </label>
        </div>
        <div>
          <label>
            Resume text:
            <br />
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={5}
              cols={60}
              required
            />
          </label>
        </div>
        <button type="submit">Add application</button>
      </form>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <table border={1} cellPadding={6}>
        <thead>
          <tr>
            <th>Company</th>
            <th>Job title</th>
            <th>Created</th>
            <th>Feedback</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {applications.map((app) => (
            <tr key={app.id}>
              <td>{app.company_name}</td>
              <td>{app.job_title}</td>
              <td>{new Date(app.created_at).toLocaleDateString()}</td>
              <td>{app.has_feedback ? "Generated" : "Not yet generated"}</td>
              <td>
                <Link to={`/applications/${app.id}`}>View</Link>{" "}
                <button onClick={() => handleDelete(app.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
