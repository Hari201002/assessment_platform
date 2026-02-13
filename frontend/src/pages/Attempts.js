import React, { useEffect, useState } from "react";
import API from "../api";
import AttemptDetail from "./AttemptDetail";

function Attempts() {
  const [data, setData] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [tests, setTests] = useState([]);

  const [filters, setFilters] = useState({
    search: "",
    test_id: "",
    status: "",
    has_duplicates: ""
  });

  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [totalPages, setTotalPages] = useState(1);

  const fetchAttempts = async () => {
    const params = {
      page: page,
      page_size: pageSize,
      search: filters.search || undefined,
      test_id: filters.test_id || undefined,
      status: filters.status || undefined,
      has_duplicates:
        filters.has_duplicates === ""
          ? undefined
          : filters.has_duplicates === "true"
    };

    const res = await API.get("/api/attempts", { params });

    setData(res.data.data);
    setTotalPages(Math.ceil(res.data.total / pageSize));
  };

  const fetchTests = async () => {
    const res = await API.get("/api/tests");
    setTests(res.data);
  };

  useEffect(() => {
    fetchAttempts();
  }, [page, filters]);

  useEffect(() => {
    fetchTests();
  }, []);

  if (selectedId) {
    return (
      <AttemptDetail
        attemptId={selectedId}
        goBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <h2>Attempts</h2>

      {/* Filters */}
      <div style={{ marginBottom: "10px" }}>
        <input
          placeholder="Search student..."
          value={filters.search}
          onChange={(e) =>
            setFilters({ ...filters, search: e.target.value })
          }
        />

        <select
          value={filters.test_id}
          onChange={(e) =>
            setFilters({ ...filters, test_id: e.target.value })
          }
        >
          <option value="">All Tests</option>
          {tests.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(e) =>
            setFilters({ ...filters, status: e.target.value })
          }
        >
          <option value="">All Status</option>
          <option value="INGESTED">INGESTED</option>
          <option value="SCORED">SCORED</option>
          <option value="DEDUPED">DEDUPED</option>
          <option value="FLAGGED">FLAGGED</option>
        </select>

        <select
          value={filters.has_duplicates}
          onChange={(e) =>
            setFilters({ ...filters, has_duplicates: e.target.value })
          }
        >
          <option value="">All</option>
          <option value="true">Has Duplicates</option>
          <option value="false">No Duplicates</option>
        </select>
      </div>

      {/* Table */}
      <table border="1">
        <thead>
          <tr>
            <th>Student</th>
            <th>Test</th>
            <th>Status</th>
            <th>Score</th>
            <th>Duplicates</th>
          </tr>
        </thead>
        <tbody>
          {data.map((a) => (
            <tr
              key={a.attempt_id}
              onClick={() => setSelectedId(a.attempt_id)}
              style={{ cursor: "pointer" }}
            >
              <td>{a.student}</td>
              <td>{a.test}</td>
              <td>{a.status}</td>
              <td>{a.score ?? "-"}</td>
              <td>{a.has_duplicates ? "Yes" : "No"}</td>
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
    </div>
  );
}

export default Attempts;