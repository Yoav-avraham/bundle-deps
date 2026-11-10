import os
import requests
import tqdm
from concurrent.futures import ThreadPoolExecutor

DOWNLOAD_WORKERS = 8


def download_file_with_progress(url, file_path):
    """
    Downloads a single file from url to file_path (no per-file progress bar).
    """
    with requests.get(url, stream=True, timeout=30) as response:
        response.raise_for_status()
        block_size = 1024  # 1 KB

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    file.write(chunk)


def download_dependencies(dependencies, output_dir, plan_files, desc, exists_set=None, verbose=False):
    """
        The function runs the shared download pipeline for any ecosystem.

        plan_files(dependency) decides what a single dependency needs and returns
        (files, skips, failed):
            files   - list of (url, filename, label) to download, or None to skip
                      the dependency without counting it as a failure
            skips   - messages to report as skipped
            failed  - True when the dependency is already broken before downloading
    """

    if exists_set is None:
        exists_set = set()

    os.makedirs(output_dir, exist_ok=True)

    failed_dependencies = []
    skipped = []
    errors = []

    def download_one(dependency):
        """Returns (package, success) or None if skipped"""
        package = f"{dependency['name']}@{dependency['version']}"

        if package in exists_set:
            skipped.append(f"{package} - already exists")
            return None

        files, skips, dependency_failed = plan_files(dependency)

        skipped.extend(skips)

        # the dependency has nothing to download and is not treated as a failure
        if files is None:
            return None

        for url, filename, label in files:

            file_path = os.path.join(output_dir, filename)

            try:
                if verbose:
                    print(f"Downloading: {label}", flush=True)
                download_file_with_progress(url, file_path)
            except requests.RequestException as error:
                errors.append(f"{package}: {error}")
                dependency_failed = True

        return package, not dependency_failed

    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        results = executor.map(download_one, dependencies)
        if not verbose:
            results = tqdm.tqdm(
                results,
                total=len(dependencies),
                desc=desc,
                unit="pack",
            )
        for result in results:
            if result is None:
                continue
            package, success = result
            if success:
                exists_set.add(package)
            else:
                failed_dependencies.append(package)

    for item in skipped:
        print(f"Skipped: {item}")
    for item in errors:
        print(f"Failed: {item}")

    if failed_dependencies:
        raise RuntimeError(
            "Failed to download dependencies: "
            + ", ".join(failed_dependencies)
        )


def plan_npm_files(dependency):
    """
        The function decides which file a single npm dependency needs
    """

    url = dependency.get("resolved")

    # without a URL there is nothing to download, but it is not a failure
    if not url:
        return None, [f"{dependency['name']} - no URL"], False

    package = f"{dependency['name']}@{dependency['version']}"

    filename = (
        dependency["name"].replace("/", "_")
        + "-"
        + dependency["version"]
        + ".tgz"
    )

    return [(url, filename, package)], [], False


def plan_uv_files(dependency, output_dir, manylinux=False):
    """
        The function decides which wheels and sdist a single uv dependency needs
    """

    package = f"{dependency['name']}@{dependency['version']}"

    files = []
    skips = []
    dependency_failed = False

    for wheel in dependency.get("wheels", []):

        url = wheel.get("url")

        if not url:
            skips.append(f"{package} - no URL")
            dependency_failed = True
            continue

        filename = os.path.basename(url)

        # with the manylinux flag, skip platform wheels that aren't manylinux
        # (pure python "any" wheels are still needed)
        if manylinux and "manylinux" not in filename and not filename.endswith("-any.whl"):
            skips.append(f"{filename} - not manylinux")
            continue

        files.append((url, filename, filename))

    sdist = dependency.get("sdist")

    if sdist:
        url = sdist.get("url")

        if url:
            filename = os.path.basename(url)

            # the sdist is skipped when a wheel already produced the same file
            if not os.path.exists(os.path.join(output_dir, filename)):
                files.append((url, filename, filename))

    return files, skips, dependency_failed


def download_npm_dependencies(dependencies, output_dir, exists_set=None, verbose=False):
    """
        The function downloads the npm dependencies from the dependencies list
    """

    return download_dependencies(
        dependencies,
        output_dir,
        plan_npm_files,
        "Downloading npm",
        exists_set,
        verbose,
    )


def download_uv_dependencies(dependencies, output_dir, exists_set=None, manylinux=False, verbose=False):
    """
        The function downloads the uv dependencies from the dependencies list
    """

    def plan(dependency):
        return plan_uv_files(dependency, output_dir, manylinux)

    return download_dependencies(
        dependencies,
        output_dir,
        plan,
        "Downloading uv",
        exists_set,
        verbose,
    )
