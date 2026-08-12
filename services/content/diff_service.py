import difflib


def _line_diff(old_text, new_text):
    """
    Compares two blocks of text line by line and returns:
    - a list of ops: [{"type": "equal"|"delete"|"insert", "line": "..."}]
    - how many lines were added
    - how many lines were removed
    """

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    ops = []
    added = 0
    removed = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "equal":
            for line in old_lines[i1:i2]:
                ops.append({"type": "equal", "line": line})

        elif tag == "delete":
            for line in old_lines[i1:i2]:
                ops.append({"type": "delete", "line": line})
                removed += 1

        elif tag == "insert":
            for line in new_lines[j1:j2]:
                ops.append({"type": "insert", "line": line})
                added += 1

        elif tag == "replace":
            for line in old_lines[i1:i2]:
                ops.append({"type": "delete", "line": line})
                removed += 1
            for line in new_lines[j1:j2]:
                ops.append({"type": "insert", "line": line})
                added += 1

    return ops, added, removed


def compute_version_diff(*, old_version, new_version):
    """
    Computes a line-based diff between two ContentVersion instances.
    old_version may be None (e.g. diffing version 1, which has no
    predecessor) — in that case everything in new_version shows as
    "insert".
    """

    old_title = old_version.title if old_version else ""
    old_body = old_version.body if old_version else ""

    title_ops, title_added, title_removed = _line_diff(
        old_title, new_version.title
    )

    body_ops, body_added, body_removed = _line_diff(
        old_body, new_version.body
    )

    return {
        "from_version": (
            old_version.version_number if old_version else None
        ),
        "to_version": new_version.version_number,
        "title_diff": title_ops,
        "body_diff": body_ops,
        "stats": {
            "lines_added": title_added + body_added,
            "lines_removed": title_removed + body_removed,
        },
    }