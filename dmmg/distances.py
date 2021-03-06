import numpy as np


def edit_dist(s1, s2):
    """Return the edit distance (insertions and deletions only) between two
    sequences s1 and s2."""
    m = len(s1)
    n = len(s2)
    return m + n - 2 * lcs_len(s1, s2, m, n)


def lcs_len(X, Y, m, n):
    """Return the lenght of the longest common subsequence between two
    sequences X and Y, where m and n are respectively |X| and |Y|."""
    if m < n:
        m, n = n, m
        X, Y = Y, X
    # C = [[0 for j in xrange(n + 1)] for i in xrange(2)]
    C = np.zeros((2, n + 1), dtype=np.int)
    for i in xrange(1, m + 1):
        for j in xrange(1, n + 1):
            if i % 2:
                if X[i - 1] == Y[j - 1]:
                    C[i % 2][j] = C[i % 2 - 1][j - 1] + 1
                else:
                    C[i % 2][j] = np.maximum(C[i % 2][j - 1], C[i % 2 - 1][j])
            else:
                if X[i - 1] == Y[j - 1]:
                    C[i % 2][j] = C[i % 2 + 1][j - 1] + 1
                else:
                    C[i % 2][j] = np.maximum(C[i % 2][j - 1], C[i % 2 + 1][j])
    return C[1][-1] if m % 2 else C[0][-1]


def lcs(X, Y, m, n):
    """Return the matrix (as a numpy 2D array) of the longest common
    subsequence between two sequences X and Y, where m and n are respectively
    |X| and |Y|."""

    # C = [[0 for j in xrange(n + 1)] for i in xrange(m + 1)]
    C = np.zeros((m + 1, n + 1), dtype=np.int)
    for i in xrange(1, m + 1):
        for j in xrange(1, n + 1):
            if X[i - 1] == Y[j - 1]:
                C[i][j] = C[i - 1][j - 1] + 1
            else:
                C[i][j] = np.maximum(C[i][j - 1], C[i - 1][j])
    return C


def lcs_print(X, Y, i, j, allign=True):
    """Print the longest common subsequence between two sequences X and Y,
    where m and n are respectively |X| and |Y|. If allign is set to True
    (default) the print function will print also the gaps as '~'.
    Example: 'abaco' and 'abbacchio' will generate 'a~ba~c~~o'."""
    C = lcs(X, Y, i, j)
    lcs_str = ''
    while True:
        if i == 0 or j == 0:
            return lcs_str
        elif X[i - 1] == Y[j - 1]:
            lcs_str = X[i - 1] + lcs_str
            i -= 1
            j -= 1
        else:
            if C[i][j - 1] > C[i - 1][j]:
                j -= 1
            else:
                i -= 1
            if allign:
                lcs_str = '~' + lcs_str


def lcs_vector(X, Y, i, j):
    """Return a list of pairs, each pair contains the starting element and the
    length for each continuos subsequence found.
    Example: 'abbaino' and 'abbacchio' will generate the allignment
    'abba~~~i~o', lcs_vector will return [['o', 1], ['i', 1], ['a', 4]]
    """
    C = lcs(X, Y, i, j)
    lcs_vector = []
    sequence = False
    while True:
        if i == 0 or j == 0:
            if sequence and i == 0:
                lcs_vector[-1][0] = X[i]
            elif sequence and j == 0:
                lcs_vector[-1][0] = X[j]
            return lcs_vector
        elif X[i - 1] == Y[j - 1]:
            if not sequence:
                lcs_vector.append([None, 1])
                sequence = True
            else:
                lcs_vector[-1][1] += 1
            i -= 1
            j -= 1
        else:
            if sequence:
                lcs_vector[-1][0] = X[i]
                sequence = False
            if C[i][j - 1] > C[i - 1][j]:
                j -= 1
            else:
                i -= 1
