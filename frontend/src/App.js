
import React, { useState } from "react";
import Attempts from "./pages/Attempts";
import Leaderboard from "./pages/Leaderboard";

function App() {
  const [page, setPage] = useState("attempts");

  return (
    <div>
      <h1>Assessment Ops Dashboard</h1>

      <button onClick={() => setPage("attempts")}>Attempts</button>
      <button onClick={() => setPage("leaderboard")}>Leaderboard</button>

      <hr />

      {page === "attempts" && <Attempts />}
      {page === "leaderboard" && <Leaderboard />}
    </div>
  );
}

export default App;
