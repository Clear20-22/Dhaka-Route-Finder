# Dhaka Smart Route Finder

Full spec: `docs/SPEC.md`. Problem statement: `docs/PROBLEM_STATEMENT.md`. Background research and data sources: `docs/CONCEPT.md`.

## Rules

1. Search algorithm গুলো নিজে লিখবে। networkx এর shortest_path বা অন্য কোনো ready-made pathfinding ব্যবহার করবে না। NetworkX/OSMnx শুধু graph load এর জন্য।
2. সব weight `weights.yaml` থেকে আসবে, code এ কোনো সংখ্যা hardcode করবে না।
3. Spec এর বাইরে কিছু করার দরকার হলে আগে জিজ্ঞেস করবে।
4. প্রতিটা phase শেষে test চালিয়ে ফল দেখাবে, confirmation নিয়ে পরের phase এ যাবে।
