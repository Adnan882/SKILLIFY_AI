import warnings
warnings.filterwarnings("ignore", message=".*word vectors.*")

import spacy
from fuzzywuzzy import fuzz

nlp = spacy.load("en_core_web_sm")


def normalize(text: str) -> str:
    return text.strip().lower().replace("_", " ")


def check_mcq(user_answer: str, correct_answer: str, options: list[str] | None = None) -> bool:
    user_norm = normalize(user_answer)
    correct_norm = normalize(correct_answer)

    if user_norm == correct_norm:
        return True

    if options:
        letter_map = {}
        for i, opt in enumerate(options):
            letter = chr(ord("a") + i)
            letter_map[letter] = normalize(opt)

        if user_norm in letter_map and letter_map[user_norm] == correct_norm:
            return True

        for letter, opt_norm in letter_map.items():
            if user_norm.startswith(letter + ".") or user_norm.startswith(letter + ")") or user_norm.startswith(letter + " "):
                remainder = user_norm[len(letter):].lstrip(".) ").strip()
                if remainder == opt_norm:
                    return True

    ratio = fuzz.ratio(user_norm, correct_norm)
    return ratio >= 85


def check_output(user_answer: str, correct_answer: str) -> bool:
    user_norm = normalize(user_answer).replace(" ", "")
    correct_norm = normalize(correct_answer).replace(" ", "")
    return user_norm == correct_norm


def check_oneword(user_answer: str, correct_answer: str) -> bool:
    user_norm = normalize(user_answer)
    correct_norm = normalize(correct_answer)

    if user_norm == correct_norm:
        return True

    if correct_norm in user_norm or user_norm in correct_norm:
        return True

    user_doc = nlp(user_norm)
    correct_doc = nlp(correct_norm)

    user_lemmas = set(token.lemma_ for token in user_doc)
    correct_lemmas = set(token.lemma_ for token in correct_doc)

    if user_lemmas == correct_lemmas:
        return True

    ratio = fuzz.ratio(user_norm, correct_norm)
    return ratio >= 80


def check_short_answer(user_answer: str, correct_answer: str) -> bool:
    user_norm = normalize(user_answer)
    correct_norm = normalize(correct_answer)

    if user_norm == correct_norm:
        return True

    if correct_norm in user_norm or user_norm in correct_norm:
        return True

    user_doc = nlp(user_norm)
    correct_doc = nlp(correct_norm)

    similarity = user_doc.similarity(correct_doc)

    user_keywords = set(
        token.lemma_.lower()
        for token in user_doc
        if token.pos_ in ("NOUN", "PROPN", "ADJ", "VERB") and not token.is_stop
    )
    correct_keywords = set(
        token.lemma_.lower()
        for token in correct_doc
        if token.pos_ in ("NOUN", "PROPN", "ADJ", "VERB") and not token.is_stop
    )

    if not correct_keywords:
        keyword_coverage = 1.0 if similarity >= 0.6 else 0.0
    else:
        matched = user_keywords & correct_keywords
        keyword_coverage = len(matched) / len(correct_keywords)

    combined_score = 0.5 * similarity + 0.5 * keyword_coverage
    return combined_score >= 0.60


def check_answer(user_answer: str, question: dict) -> bool:
    if not user_answer or not user_answer.strip():
        return False

    q_type = question.get("type", "mcq")
    correct_answer = question["a"]
    options = question.get("options")

    if q_type == "mcq":
        return check_mcq(user_answer, correct_answer, options)
    elif q_type == "output":
        return check_output(user_answer, correct_answer)
    elif q_type == "oneword":
        return check_oneword(user_answer, correct_answer)
    elif q_type == "short":
        return check_short_answer(user_answer, correct_answer)
    else:
        return check_mcq(user_answer, correct_answer, options)
