from datetime import timedelta

SIMILARITY_THRESHOLD = 0.92


def calculate_similarity(a1, a2):
    if not a1 or not a2:
        return 0

    same = 0
    compared = 0

    for q, ans in a1.items():
        if q in a2:
            compared += 1
            if a2[q] == ans:
                same += 1

    if compared == 0:
        return 0

    return same / compared


def is_duplicate(new_attempt, existing_attempt):
    # 7 minute rule
    time_diff = abs(new_attempt.started_at - existing_attempt.started_at)

    if time_diff > timedelta(minutes=7):
        return False

    similarity = calculate_similarity(
        new_attempt.answers,
        existing_attempt.answers
    )

    if similarity >= SIMILARITY_THRESHOLD:
        return True

    return False
