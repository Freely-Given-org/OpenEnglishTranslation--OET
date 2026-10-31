# SPDX-License-Identifier: MPL-2.0
"""2026-10-22: retain only occurrence pairs shared by all best sequence alignments."""

def certain_matches(matrix):
    """Return source -> target indexes only when every best alignment agrees."""
    n, m = len(matrix), len(matrix[0]) if matrix else 0
    if not n or not m:
        return {}
    forward = [[0]*(m+1) for _ in range(n+1)]
    backward = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n):
        for j in range(m):
            forward[i+1][j+1] = max(forward[i][j+1], forward[i+1][j],
                                     forward[i][j] + (matrix[i][j] or 0))
    for i in range(n-1, -1, -1):
        for j in range(m-1, -1, -1):
            backward[i][j] = max(backward[i+1][j], backward[i][j+1],
                                  backward[i+1][j+1] + (matrix[i][j] or 0))
    best, result = forward[n][m], {}
    for i in range(n):
        if any(forward[i][j] + backward[i+1][j] == best for j in range(m+1)):
            continue  # At least one best alignment leaves this occurrence unmatched.
        targets = [j for j in range(m) if matrix[i][j]
                   and forward[i][j] + matrix[i][j] + backward[i+1][j+1] == best]
        if len(targets) == 1:
            result[i] = targets[0]
    return result
