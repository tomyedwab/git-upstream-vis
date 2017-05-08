#!/usr/bin/env python
import asciitree
from collections import defaultdict
import subprocess

branch_map = defaultdict(lambda: {
    "name": "",
    "active": False,
    "commit_sha": "",
    "commit_message": "",
    "upstream_note": None,
    "upstream_branch": None,
    "children": []
})

for row in subprocess.check_output(["git", "branch", "-vv"]).split("\n"):
    if not row:
        continue

    active = row[0] == "*"

    upstream_idx1 = row.index("[")
    upstream_idx3 = row[upstream_idx1:].index("]") + upstream_idx1
    try:
        upstream_idx2 = row[upstream_idx1:].index(":") + upstream_idx1
    except ValueError:
        upstream_idx2 = upstream_idx3

    upstream_branch = row[upstream_idx1 + 1 : upstream_idx2]
    upstream_note = row[upstream_idx2 + 2 : upstream_idx3]

    branch_name = row[2 : upstream_idx1 - 8].strip()
    commit_sha = row[upstream_idx1 - 8 : upstream_idx1 - 1]
    commit_message = row[upstream_idx3 + 2 : ]

    if upstream_note == "gone":
        upstream_branch = "%s [gone]" % upstream_branch
        upstream_note = None

    branch_map[branch_name].update({
        "name": branch_name,
        "active": active,
        "commit_sha": commit_sha,
        "commit_message": commit_message,
        "upstream_note": upstream_note,
        "upstream_branch": upstream_branch,
    })

    if not upstream_branch:
        upstream_branch = ""

    branch_map[upstream_branch]["name"] = upstream_branch
    branch_map[upstream_branch]["children"].append(branch_name)

def _format_line(branch):
    style = None
    if branch["active"]:
        style = "0;32"
    elif branch["name"].endswith("[gone]"):
        style = "0;31"
    elif branch["name"].startswith("origin/"):
        style = "0;34"

    line = [
        branch["name"],
        " *" if branch["active"] else "",
        "$",
        "\x1b[%sm$" % style if style else "$",
        branch["commit_sha"],
        " ",
        branch["commit_message"],
        " [%s]" % branch["upstream_note"] if branch["upstream_note"] else "",
    ]
    return "".join(line)

def _create_tree(branch):
    return {
        _format_line(branch_map[child]): _create_tree(branch_map[child])
        for child in branch["children"]
    }

branch_map[""]["children"] = [
    branch["name"]
    for branch in branch_map.itervalues()
    if not branch["upstream_branch"]
]

root = {
    "": _create_tree(branch_map[""])
}

tree_lines = asciitree.LeftAligned()(root).split("\n")
max_index = max([row.find("$") for row in tree_lines])
tree_lines = map(
    lambda row: (
        row.split("$")[0]
            # Pad to the maximum width of the column up until the $
            .ljust(max_index+1)
            # Move styling to the front of the line
            .replace(
                "+--",
                row.split("$")[1] + "+--") +
        # Rest of the line, excluding style information
        row.split("$")[2] +
        # Clear styling at the end of the line
        "\x1b[0m"),
    filter(lambda row: "$" in row, tree_lines))
print "\n".join(tree_lines)
