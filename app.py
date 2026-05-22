"""Hazard Hub entrypoint for local development."""

from app import create_app
from app.services.classifier import NaiveBayesClassifier, classify_priority, nb_classifier

app = create_app()


if __name__ == "__main__":
    print("\n" + "=" * 62)
    print("  Hazard Hub - Flask Backend  (Naive Bayes Classifier)")
    print(f"  Vocab size  : {len(nb_classifier.vocabulary)} words")
    print(f"  Classes     : {NaiveBayesClassifier.CLASSES}")
    print(f"  Train size  : {len(NaiveBayesClassifier.TRAINING_DATA)} samples")
    print("\n  Self-test results:")
    for txt, exp in [
        ("fire explosion chemical gas leak emergency danger fatal", "High"),
        ("slip wet floor broken equipment near miss noise", "Medium"),
        ("minor suggestion cleanliness improvement feedback", "Low"),
    ]:
        _, r = classify_priority(txt)
        ok = "OK" if r["priority"] == exp else "X"
        print(f"  {ok}  {r['priority']:6s} ({r['confidence']*100:4.1f}%) | {txt[:50]}")
    print("\n  Diagnostic : http://localhost:5000/check")
    print("  Login      : http://localhost:5000/login")
    print("=" * 62 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
