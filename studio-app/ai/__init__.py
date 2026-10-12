"""Studio Intelligence AI layer.

A grounded assistant for the generated reviews:

* ``metrics_pack``  - a compact, JSON-serialisable snapshot of every headline
  metric in a run (the only context the model ever sees).
* ``qa``            - a deterministic question-answering engine that resolves
  most data questions with zero model tokens.
* ``llm``           - a provider-agnostic OpenAI-compatible client, enabled by
  environment keys; the layer degrades gracefully without one.
* ``store``         - persistence for chat history, report edits and the
  answer cache; Supabase (PostgREST) when configured, SQLite otherwise.
* ``agent``         - orchestrates the three: deterministic first, model only
  where it adds value, every number traceable to the metrics pack.
"""
