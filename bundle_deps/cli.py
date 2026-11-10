import argparse

from bundle_deps.export import export_project


def create_parser():
    """
        The function creates the parser for the flags of the cli tool
    """

    parser = argparse.ArgumentParser(description="Package bundling tool")
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument("--commit-sha" , help="Commit SHA to compare current dependencies against")
    parser.add_argument("--latest-commit", action="store_true", help="Get the latest Commit SHA to compare current dependencies against")
    parser.add_argument("--verbose","-v" ,action="store_true", help="Print each dependency as it is downloaded instead of showing a progress bar")
    parser.add_argument("--manylinux", action="store_true", help="Download only manylinux wheels (plus pure python wheels) for uv dependencies")
    parser.add_argument("--no-pack", action="store_true", help="Does not pack the dependencies in .tar.gz")
    parser.add_argument("--bundle-name", help="Allows to choose the bundle name")
    parser.add_argument("--output-dir", help="Allows to choose the output dir for the bundle")
    
    return parser


def main():

    # creates the parser and get the args
    parser = create_parser()
    args = parser.parse_args()
    try:
        export_project(args.project_path, args.commit_sha, args.latest_commit, args.manylinux, args.verbose, args.no_pack, args.bundle_name, args.output_dir)

    except (FileNotFoundError, NotADirectoryError, RuntimeError) as error:
        print(f"error: {error}")
        raise SystemExit(1)
