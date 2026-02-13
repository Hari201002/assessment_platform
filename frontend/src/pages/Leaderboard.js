import React, { useEffect, useState } from "react";
import API from "../api";

function Leaderboard() {
  const [tests, setTests] = useState([]);
  const [selectedTest, setSelectedTest] = useState("");
  const [data, setData] = useState([]);

  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchTests = async () => {
      const res = await API.get("/api/tests");
      setTests(res.data);
    };
    fetchTests();
  }, []);

  const fetchLeaderboard = async () => {
    if (!selectedTest) return;

    const res = await API.get("/api/leaderboard", {
      params: {
        test_id: selectedTest,
        page: page,
        page_size: pageSize
      }
    });

    setData(res.data.data);
    setTotalPages(Math.ceil(res.data.total / pageSize));
  };

  useEffect(() => {
    if (selectedTest) {
      fetchLeaderboard();
    }
  }, [page]);

  return (
    <div>
      <h2>Leaderboard</h2>

      {/* Test Select */}
      <select
        value={selectedTest}
        onChange={(e) => {
          setSelectedTest(e.target.value);
          setPage(1);
        }}
      >
        <option value="">Select Test</option>
        {tests.map((test) => (
          <option key={test.id} value={test.id}>
            {test.name}
          </option>
        ))}
      </select>

      <button onClick={fetchLeaderboard}>Load</button>

      {/* Table */}
      {data.length > 0 && (
        <>
          <table border="1" style={{ marginTop: "20px" }}>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Student ID</th>
                <th>Score</th>
                <th>Accuracy</th>
                <th>Net Correct</th>
                <th>Submitted At</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item, index) => (
                <tr key={item.attempt_id}>
                  <td>{(page - 1) * pageSize + index + 1}</td>
                  <td>{item.student_id}</td>
                  <td>{item.score}</td>
                  <td>{item.accuracy}</td>
                  <td>{item.net_correct}</td>
                  <td>{item.submitted_at}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div style={{ marginTop: "10px" }}>
            <button disabled={page === 1} onClick={() => setPage(page - 1)}>
              Prev
            </button>

            <span> Page {page} of {totalPages} </span>

            <button
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default Leaderboard;