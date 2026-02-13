import React, { useEffect, useState } from "react";
import API from "../api";

function AttemptDetail({ attemptId, goBack }) {
  const [data, setData] = useState(null);
  const [showPayload, setShowPayload] = useState(false);

  const fetchDetail = async () => {
    const res = await API.get(`/api/attempts/${attemptId}`);
    setData(res.data);
  };

  const recompute = async () => {
    await API.post(`/api/attempts/${attemptId}/recompute`);
    fetchDetail();
  };

  const flagAttempt = async () => {
    const reason = prompt("Enter flag reason:");
    if (!reason) return;

    await API.post(`/api/attempts/${attemptId}/flag`, {
      reason: reason
    });

    fetchDetail();
  };

  useEffect(() => {
    fetchDetail();
  }, [attemptId]);

  if (!data) return <div>Loading...</div>;

  return (
    <div>
      <button onClick={goBack}>← Back</button>

      <h2>Attempt Detail</h2>

      <p><b>Student:</b> {data.student.name}</p>
      <p><b>Email:</b> {data.student.email}</p>
      <p><b>Test:</b> {data.test.name}</p>
      <p><b>Status:</b> {data.status}</p>

      {/* Score Breakdown */}
      <h3>Score Breakdown</h3>
      {data.score ? (
        <div>
          <p>Correct: {data.score.correct}</p>
          <p>Wrong: {data.score.wrong}</p>
          <p>Skipped: {data.score.skipped}</p>
          <p>Accuracy: {data.score.accuracy}</p>
          <p>Net Correct: {data.score.net_correct}</p>
          <p>Total Score: {data.score.score}</p>
        </div>
      ) : (
        <p>No score available</p>
      )}

      {/* Duplicate Thread */}
      <h3>Duplicate Thread</h3>
      <ul>
        {data.duplicate_thread.map((item) => (
          <li key={item.attempt_id}>
            {item.attempt_id} - {item.status}
          </li>
        ))}
      </ul>

      {/* Flags */}
      <h3>Flags</h3>
      <ul>
        {data.flags.map((flag) => (
          <li key={flag.id}>
            {flag.reason} ({flag.created_at})
          </li>
        ))}
      </ul>

      {/* Raw Payload Collapsible */}
      <h3>
        Raw Payload
        <button onClick={() => setShowPayload(!showPayload)}>
          {showPayload ? "Hide" : "Show"}
        </button>
      </h3>

      {showPayload && (
        <pre style={{ background: "#f4f4f4", padding: "10px" }}>
          {JSON.stringify(data.raw_payload, null, 2)}
        </pre>
      )}

      <br />
      <button onClick={recompute}>Recompute</button>
      <button onClick={flagAttempt}>Flag</button>
    </div>
  );
}

export default AttemptDetail;
