"""Presentation order shared by report generation and source reconciliation."""
CHAPTER_ORDER = (
    'overview', 'sales', 'class', 'instructor', 'lapse', 'format',
    'cancels', 'leads', 'behaviour', 'review',
)


def chapter_number(cid, default=0):
    return CHAPTER_ORDER.index(cid) + 1 if cid in CHAPTER_ORDER else default


def ordered(chapters):
    """Overview leads; an available Performance Review always closes the report."""
    return sorted(chapters, key=lambda ch: chapter_number(ch['id'], len(CHAPTER_ORDER) + 1))
