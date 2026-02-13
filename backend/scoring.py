def compute_score(test, student_answers):

    answer_key = test.answer_key
    config = test.negative_marking

    correct = 0
    wrong = 0
    skipped = 0

    for question, correct_answer in answer_key.items():

        student_answer = student_answers.get(question)

        if student_answer is None or student_answer == "SKIP":
            skipped += 1
        elif student_answer == correct_answer:
            correct += 1
        else:
            wrong += 1

    attempted = correct + wrong

    accuracy = (correct / attempted * 100) if attempted > 0 else 0
    net_correct = correct - wrong

    score = (
        correct * config["correct"] +
        wrong * config["wrong"] +
        skipped * config["skip"]
    )

    return {
        "correct": correct,
        "wrong": wrong,
        "skipped": skipped,
        "accuracy": round(accuracy, 2),
        "net_correct": net_correct,
        "score": score,
        "explanation": {
            "config": config,
            "counts": {
                "correct": correct,
                "wrong": wrong,
                "skipped": skipped
            }
        }
    }
