"""Naive Bayes classifier and training data helpers."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path

DEFAULT_TRAINING_DATA_FILE = Path(__file__).resolve().parents[2] / "training_data.json"
TRAINING_DATA_FILE = str(DEFAULT_TRAINING_DATA_FILE)


class NaiveBayesClassifier:
    """Multinomial Naive Bayes with Laplace smoothing."""

    CLASSES = ["High", "Medium", "Low"]

    TRAINING_DATA = [
        ("fire explosion flammable chemical hazard emergency danger critical", "High"),
        ("electrical fire exposed wire short circuit spark ignition", "High"),
        ("toxic chemical spill gas leak dangerous fume exposure fatal", "High"),
        ("worker injured accident fatal injury hospitalization ambulance", "High"),
        ("radiation exposure nuclear hazardous material contamination", "High"),
        ("building collapse structure failure emergency evacuation", "High"),
        ("explosion risk gas leak pressure vessel rupture boiler", "High"),
        ("severe injury broken bone fracture amputation critical condition", "High"),
        ("electrical shock electrocution live wire unprotected circuit", "High"),
        ("chemical burn acid alkaline corrosive exposure skin eye", "High"),
        ("fire in warehouse storage area flammable material ignited", "High"),
        ("emergency evacuation required immediate danger life threatening", "High"),
        ("oxygen deficient confined space asphyxiation fatal risk", "High"),
        ("heavy machine caught between crushing injury entanglement", "High"),
        ("fall from height scaffold ladder roof serious injury", "High"),
        ("electrical panel overloaded circuit breaker fire risk immediate", "High"),
        ("toxic gas hydrogen sulfide ammonia chlorine release worker exposed", "High"),
        ("uncontrolled chemical reaction hazardous runaway exothermic", "High"),
        ("forklift accident collision pedestrian serious injury emergency", "High"),
        ("lockout tagout failure energy release unexpected start injury", "High"),
        ("pressurized tank rupture explosion risk immediate shutdown required", "High"),
        ("worker trapped pinned under heavy object critical rescue needed", "High"),
        ("acid spill large area contamination chemical emergency response", "High"),
        ("scaffold collapse multiple workers danger critical structural failure", "High"),
        ("gas cylinder leaking flammable explosive atmosphere ignition source", "High"),
        ("slip trip wet floor puddle water walkway uneven surface", "Medium"),
        ("broken equipment machinery malfunction not working needs repair", "Medium"),
        ("ergonomic issue lifting heavy loads awkward posture strain", "Medium"),
        ("spill minor leak needs cleanup contained area", "Medium"),
        ("noise excessive loud machinery hearing protection required", "Medium"),
        ("poor housekeeping cluttered workstation blocked aisle", "Medium"),
        ("missing safety sign warning label faded unclear", "Medium"),
        ("vibration hand arm whole body exposure repetitive", "Medium"),
        ("heat stress high temperature dehydration rest area needed", "Medium"),
        ("biological contamination mold bacteria pest infestation", "Medium"),
        ("tripping hazard cables exposed cord floor pathway obstruction", "Medium"),
        ("worn protective equipment PPE defective needs replacement", "Medium"),
        ("poor lighting inadequate visibility dark area working", "Medium"),
        ("manual handling injury back pain musculoskeletal disorder", "Medium"),
        ("unsafe scaffold incomplete missing guardrail handrail", "Medium"),
        ("blocked emergency exit fire door not closing properly", "Medium"),
        ("dust accumulation respiratory hazard ventilation inadequate", "Medium"),
        ("missing fire extinguisher not inspected overdue expired", "Medium"),
        ("near miss incident no injury narrow escape recorded", "Medium"),
        ("equipment guard missing machine guarding removed bypassed", "Medium"),
        ("chemical storage improper flammable material not labeled", "Medium"),
        ("forklift speeding pedestrian pathway shared area unsafe", "Medium"),
        ("electrical cord frayed damaged insulation minor repair required", "Medium"),
        ("slip hazard oil grease floor needs anti-slip treatment", "Medium"),
        ("broken step stair railing loose damaged walkway hazard", "Medium"),
        ("suggestion improvement workflow process efficiency productivity", "Low"),
        ("minor cleanliness issue trash not collected cleaning needed", "Low"),
        ("small scratch dent minor damage cosmetic no safety risk", "Low"),
        ("idea feedback recommendation better practice workplace", "Low"),
        ("general concern comment feedback observation non-urgent", "Low"),
        ("maintenance request routine scheduled preventive upkeep", "Low"),
        ("broken chair desk lamp minor office furniture needs fixing", "Low"),
        ("parking area improvement request signage parking lot", "Low"),
        ("cafeteria food quality suggestion employee welfare comfort", "Low"),
        ("administrative concern paperwork documentation process", "Low"),
        ("air conditioning temperature comfort office environment", "Low"),
        ("request for additional equipment tool convenience not urgent", "Low"),
        ("minor communication issue team coordination improvement", "Low"),
        ("suggestion for training program schedule employee development", "Low"),
        ("cosmetic repair paint wall ceiling minor aesthetic issue", "Low"),
        ("general housekeeping reminder cleanliness tidiness area", "Low"),
        ("suggestion break room improvement coffee machine request", "Low"),
        ("feedback on work schedule rotation minor adjustment", "Low"),
        ("request for new signage direction board wayfinding non-critical", "Low"),
        ("improvement idea safety poster awareness campaign", "Low"),
        ("request bulletin board notice board update posting area", "Low"),
        ("comfort request fan ventilation minor temperature adjustment", "Low"),
        ("feedback on meeting frequency schedule calendar update", "Low"),
        ("minor cosmetic concern floor mat placement comfort request", "Low"),
        ("suggestion update break schedule locker room improvement", "Low"),
    ]

    def __init__(self):
        self.class_log_priors = {}
        self.word_log_likelihoods = {c: defaultdict(float) for c in self.CLASSES}
        self.vocabulary = set()
        self._train()

    @staticmethod
    def tokenize(text: str) -> list[str]:
        text = str(text).lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        return [w for w in text.split() if len(w) > 1]

    def _train(self) -> None:
        class_word_lists = defaultdict(list)
        class_doc_counts = defaultdict(int)

        for text, label in self.TRAINING_DATA:
            tokens = self.tokenize(text)
            class_word_lists[label].extend(tokens)
            class_doc_counts[label] += 1
            self.vocabulary.update(tokens)

        total_docs = sum(class_doc_counts.values())
        vocab_size = len(self.vocabulary)

        for cls in self.CLASSES:
            self.class_log_priors[cls] = math.log(
                class_doc_counts[cls] / total_docs
            )

            freq = defaultdict(int)
            for word in class_word_lists[cls]:
                freq[word] += 1
            total_words = sum(freq.values()) + vocab_size

            for word in self.vocabulary:
                self.word_log_likelihoods[cls][word] = math.log(
                    (freq.get(word, 0) + 1) / total_words
                )
            self.word_log_likelihoods[cls]["<UNK>"] = math.log(1 / total_words)

    def predict(self, text: str) -> dict:
        tokens = self.tokenize(text)
        if not tokens:
            return {
                "priority": "Low",
                "confidence": 1.0,
                "scores": {"High": 0.0, "Medium": 0.0, "Low": 1.0},
                "algorithm": "Naive Bayes (Multinomial, Laplace smoothing)",
            }

        log_scores = {}
        for cls in self.CLASSES:
            score = self.class_log_priors[cls]
            for token in tokens:
                ll = self.word_log_likelihoods[cls]
                score += ll[token] if token in ll else ll["<UNK>"]
            log_scores[cls] = score

        max_s = max(log_scores.values())
        exps = {c: math.exp(s - max_s) for c, s in log_scores.items()}
        total = sum(exps.values())
        probs = {c: exps[c] / total for c in self.CLASSES}

        best = max(probs, key=probs.get)
        return {
            "priority": best,
            "confidence": round(probs[best], 4),
            "scores": {
                "High": round(probs["High"], 4),
                "Medium": round(probs["Medium"], 4),
                "Low": round(probs["Low"], 4),
            },
            "algorithm": "Naive Bayes (Multinomial, Laplace smoothing)",
        }


nb_classifier = NaiveBayesClassifier()


def _get_training_path() -> Path:
    return Path(TRAINING_DATA_FILE) if TRAINING_DATA_FILE else DEFAULT_TRAINING_DATA_FILE


def load_custom_training_data() -> list[dict]:
    path = _get_training_path()
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_custom_training_data(data: list[dict]) -> None:
    path = _get_training_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_merged_training_data() -> list[dict]:
    custom = load_custom_training_data()
    base = [
        {"id": i, "text": text, "priority": priority, "source": "built-in"}
        for i, (text, priority) in enumerate(NaiveBayesClassifier.TRAINING_DATA)
    ]
    offset = len(base)
    custom_merged = [
        {
            "id": offset + i,
            "text": item["text"],
            "priority": item["priority"],
            "source": "custom",
        }
        for i, item in enumerate(custom)
    ]
    return base + custom_merged


def init_classifier(app) -> None:
    global TRAINING_DATA_FILE
    TRAINING_DATA_FILE = app.config.get("TRAINING_DATA_FILE", TRAINING_DATA_FILE)
    nb_classifier.custom_training_data = load_custom_training_data()
    nb_classifier.get_all_training_data = get_merged_training_data


def classify_priority(text: str, hazard_type: str = "", risk_level: str = "") -> tuple[str, dict]:
    combined = " ".join(filter(None, [str(text), str(hazard_type), str(risk_level)]))
    result = nb_classifier.predict(combined)
    return result["priority"], result
