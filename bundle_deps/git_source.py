import os
import tarfile
import subprocess

from bundle_deps.utils import temporary_directory


def get_git_url():
    """Resolve the repo URL dynamically: CI env vars first, then the origin remote."""
    server = os.getenv("GITHUB_SERVER_URL")
    repo = os.getenv("GITHUB_REPOSITORY")
    if server and repo:
        return f"{server}/{repo}.git"
    return subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def fetch_git_by_sha(git_url, commit_sha, latest_commit=False, git_path="remote_git"):
    """
        The function clones a repo from a git url and specific commit
        into git_path
    """

    # the clone and the archive live in a temp dir that is removed at the end
    with temporary_directory() as work_dir:

        temp_git = os.path.join(work_dir, "temp_git")
        repo_archive = os.path.join(work_dir, "repo.tar")

        try:
            # clone the repo and fetch the specific commit as an archive
            subprocess.run(["git", "clone", "--no-checkout", git_url, temp_git],check=True)

            commit_sha = "HEAD^" if latest_commit else commit_sha

            print(f"Processing the commit: {commit_sha}")

            subprocess.run(["git", "-C", temp_git, "archive", "--format=tar", commit_sha, "-o", repo_archive],check=True)

            # make dir for the unzipped archive
            os.makedirs(git_path, exist_ok=True)

            # open the repo archive 
            with tarfile.open(repo_archive, "r") as tar:
                tar.extractall(git_path)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Failed to fetch git commit {commit_sha}") from error

    return git_path
