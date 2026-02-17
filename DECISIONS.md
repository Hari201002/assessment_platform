

```markdown
# Engineering Decisions

## 1. Gmail Normalization
Emails are normalized to lowercase.
For Gmail addresses, alias after "+" is removed.
Example:
name+abc@gmail.com → name@gmail.com

## 2. Student Identity Fallback
If email is missing:
- Phone number digits are normalized and used as identity.

## 3. Deduplication Strategy

Two attempts are considered duplicates if:

- Same student identity
- Same test
- started_at within 7 minutes
- Answer similarity ≥ 0.92

Similarity logic:
same_answer_count / compared_questions

No external fuzzy libraries used.

## 4. Partial Submissions

If submitted_at missing:
- Still ingested
- Status remains INGESTED until recomputed

## 5. Malformed Timestamps

If timestamp parsing fails:
- Event skipped
- Logged with error channel

## 6. Score Calculation

Using tests.negative_marking JSON:
{
  "correct": X,
  "wrong": Y,
  "skip": Z
}

accuracy stored as numeric
Full explanation JSON stored.

## 7. Leaderboard Ranking Priority

1. Highest score
2. Higher accuracy
3. Higher net_correct
4. Earlier submission

Only best attempt per student counted.

## 8. Logging Design

Monolog-style structured JSON:

Fields:
- timestamp
- level
- message
- channel
- context
- extra

Every request has unique request_id.

Logged:
- Request start/end
- Dedup decision
- Score computation
- Errors

## 9. Pagination Strategy

Backend supports page & page_size.
Frontend integrates page navigation.

---

System prioritizes correctness, observability, and traceability.
