import hashlib
import os
import time
from typing import Any

import requests

GITHUB_USER = os.getenv("USER_NAME", "wh0crypt")
TOKEN = os.getenv("ACCESS_TOKEN", "TOKEN_HERE")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def repo_exists(full_name: str) -> bool:
    """Check if a GitHub repository exists."""

    r = requests.get(f"https://api.github.com/repos/{full_name}", headers=HEADERS)
    return r.status_code != 404


def sha256_repo(repo: str) -> str:
    """Generate a SHA-256 hash for a repository name."""

    return hashlib.sha256(repo.encode()).hexdigest()


def fetch_user_events(user: str) -> Any:
    """Fetch all public events for a user."""

    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{user}/events?page={page}&per_page=100",
            headers=HEADERS,
        )
        if not r.json():
            break

        yield from r.json()
        page += 1
        time.sleep(0.3)


def build_deleted_repo_archive() -> None:
    """Build an archive of deleted repositories the user has contributed to."""

    repos = {}
    for event in fetch_user_events(GITHUB_USER):
        repo = event["repo"]["name"]  # owner/repo
        if repo not in repos:
            repos[repo] = {
                "my_commits": 0,
                "loc_add": 0,
                "loc_del": 0,
            }

        if event["type"] == "PushEvent":
            for commit in event["payload"].get("commits", []):
                if commit.get("author", {}).get("name") == GITHUB_USER:
                    repos[repo]["my_commits"] += 1
                    # Changes sometimes still exist
                    # but usually not for deleted repos
                    # Can be left as 0 if not available
                    repos[repo]["loc_add"] += commit.get("additions", 0)
                    repos[repo]["loc_del"] += commit.get("deletions", 0)

    deleted = {}
    for repo, stats in repos.items():
        if not repo_exists(repo):
            deleted[repo] = stats

    # Create output file
    with open("cache/repository_archive.txt", "w") as f:
        string1 = (
            "This is an archive of all of the deleted repositories"
            + "I have contributed to.\n\n"
        )
        f.write(string1)
        string2 = (
            "repository (hashed)  total commits  my commits  LOC added by"
            + "me  LOC deleted by me\n"
        )
        f.write(string2)
        string3 = (
            "         \\                \\                \\           \\"
            + "___________  \\\n"
        )
        f.write(string3)
        string4 = (
            "          \\                \\                \\____________"
            + "_________ \\  \\\n"
        )
        f.write(string4)
        string5 = (
            "           \\                \\_____________________________"
            + "______  \\ \\  \\\n"
        )
        f.write(string5)
        string6 = (
            "____________\\______________________________________________"
            + "_____\\__\\_\\__\\____\n"
        )
        f.write(string6)

        for repo, stats in deleted.items():
            h = sha256_repo(repo)
            total = "X"  # deleted repos → not available
            mine = stats["my_commits"]
            add = stats["loc_add"]
            dele = stats["loc_del"]
            f.write(f"{h} {total} {mine} {add} {dele}\n")

    print("Created file: cache/repository_archive.txt")


if __name__ == "__main__":
    build_deleted_repo_archive()
