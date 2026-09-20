# Experiments

The quick benchmark uses agent counts 5, 10, and 15 with seeds 0 through 4.
Each algorithm receives the same instance for a `(count, seed)` pair. CBS has a
0.6 second per-instance timeout. All failures and timeouts remain in the CSV.

Runtime plots show median runtime across all runs. Cost plots contain only
successful, independently validated, conflict-free solutions and therefore
exclude conflict-unaware Independent A*.
