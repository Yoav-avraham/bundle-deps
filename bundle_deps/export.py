import os
import shutil
from datetime import datetime

from bundle_deps.utils import runtime_count, temporary_directory, validate_project_path
from bundle_deps.locks import (
    find_lock_files,
    gather_npm_dependencies_from_locks,
    gather_uv_dependencies_from_lockfiles,
)
from bundle_deps.download import download_npm_dependencies, download_uv_dependencies
from bundle_deps.archive import create_bundle_archive, create_dependencies_archive
from bundle_deps.git_source import get_git_url, fetch_git_by_sha

COMMIT_SHA = os.getenv("GITHUB_SHA") or "example-sha"


@runtime_count
def export_project(project_path, commit_sha=None, latest_commit=False, manylinux=False, verbose=False, no_pack=False, bundle_name = None, output_dir=None):
    """
        The function handles the export flow from getting the dependencies
        from the lockfiles to downloading it and creating a bundle
    """
    
    # check if the projects path exists or a dir
    project_path = validate_project_path(project_path)

    # get all the paths of the lock files
    npm_lock_files, uv_lock_files = find_lock_files(project_path)

    # if theres no lock files stop
    if not npm_lock_files and not uv_lock_files:
        print("No lock files found")
        return

    # get the timestamp for the bundle name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if bundle_name is None:
        bundle_name = f"{timestamp}-{COMMIT_SHA}"

    # gather all of the dependencies from lockfiles
    npm_dependencies, _ = gather_npm_dependencies_from_locks(npm_lock_files)
    uv_dependencies, _ = gather_uv_dependencies_from_lockfiles(uv_lock_files)

    # every dependency is downloaded into a temp dir that is removed at the end
    with temporary_directory() as temp_dir:

        bundle_dir = os.path.join(temp_dir, bundle_name)

        # make paths for seperate dirs for uv and npm
        npm_dir = os.path.join(bundle_dir, "npm")
        uv_dir = os.path.join(bundle_dir, "uv")

        if commit_sha or latest_commit:

            # clone the git repo from a specific sha into its own temp dir
            with temporary_directory() as git_temp_dir:

                git_path = os.path.join(git_temp_dir, "remote_git")

                # clone the git repo of the specific sha
                fetch_git_by_sha(get_git_url(), commit_sha, latest_commit, git_path)

                # get lock files
                git_npm_lock_files, git_uv_lock_files = find_lock_files(git_path)

                # gather all of the dependencies in
                _, git_npm_set = gather_npm_dependencies_from_locks(git_npm_lock_files)
                _, git_uv_set = gather_uv_dependencies_from_lockfiles(git_uv_lock_files)

            # download only the dependencies that the old commit does not have
            download_npm_dependencies(npm_dependencies, npm_dir, git_npm_set, verbose=verbose)
            download_uv_dependencies(uv_dependencies, uv_dir, git_uv_set, manylinux, verbose)
        else:
            # download all of the dependencies
            download_npm_dependencies(npm_dependencies, npm_dir, verbose=verbose)
            download_uv_dependencies(uv_dependencies, uv_dir, manylinux=manylinux, verbose=verbose)

        # if theres no uv dependencies remove the dir
        if len(os.listdir(uv_dir)) == 0:
            print("No uv dependencies required download")
            os.rmdir(uv_dir)

        #  if theres no npm dependencies remove the dir
        if len(os.listdir(npm_dir)) == 0:
            print("No npm dependencies required download")
            os.rmdir(npm_dir)
        else:
            # create npm-dependencies.tgz
            npm_archive = os.path.join(bundle_dir, "npm-dependencies.tgz")

            create_dependencies_archive(npm_dir, npm_archive)

            # remove original npm dir
            shutil.rmtree(npm_dir)

        if not os.listdir(bundle_dir):
            print("No dependencies required download")
            return

        if no_pack:
            # copy the dependencies out of the temp dir as a plain folder
            output_path = os.path.join(output_dir or os.getcwd(), bundle_name)
            shutil.copytree(bundle_dir, output_path, dirs_exist_ok=True)

            print(f"Dependencies copied to: {output_path}")
        else:
            # pack the dependencies and copy the archive out of the temp dir
            archive_path = os.path.join(temp_dir, f"{bundle_name}.tar.gz")
            create_bundle_archive(bundle_dir, archive_path)

            if output_dir is None:
                output_path = os.path.join(os.getcwd(), f"{bundle_name}.tar.gz")
            else:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{bundle_name}.tar.gz")

            shutil.copy2(archive_path, output_path)

            print(f"Bundle created: {output_path}")
