import os
import json
import tomllib


def find_lock_files(project_path):
    """
        The function finds all of the lock files in the project
        and returns their paths
    """
    
    # init lists for uv and npm locks paths
    uv_lock_files = []
    npm_lock_files = []

    # recursive walk in the project dir in search of lock files
    for root, dirs, files in os.walk(project_path):

        # check each file 
        for file in files:

            # if file is package-lock or uv.lock append to list
            if file == "package-lock.json":
                npm_lock_files.append(os.path.join(root, file))

            elif file == "uv.lock":
                uv_lock_files.append(os.path.join(root, file))

    return npm_lock_files, uv_lock_files


def extract_npm_dependencies(lock_path):
    """
        The function takes the npm dependencies , their versions ,
        integrity and url
    """

    # init list for the dependencies
    dependencies = []
    dependencies_set = set()

    try:
        # open the json file and load it into a dict
        with open(lock_path, "r", encoding="utf-8") as file:
            lock_data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Failed to read npm lock files: {lock_path}"
        ) from error

    # check each item in the dict
    for path, info in lock_data["packages"].items():

        # if the item doesnt start with node_modules skip
        if "node_modules/" not in path:
            continue

        # split the name from the path
        package_name = path.split("node_modules/")[-1]

        # append the dependencies to the list
        dependencies.append({
            "name": package_name,
            "version": info.get("version"),
            "resolved": info.get("resolved"),
            "integrity": info.get("integrity")
        })
        
        dependencies_set.add(f"{package_name}@{info.get("version")}")

    return dependencies , dependencies_set


def extract_uv_dependencies(lock_path):
    """
        The function extracts uv dependencies from the lock file
    """
    
    # init list for dependencies
    dependencies = []
    dependencies_set = set()
    try:  

        # open the uv.lock file and load it into a dict
        with open(lock_path, "rb") as file:
            lock_data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise RuntimeError(
            f"Failed to read uv lock files {lock_path}"
        ) from error

    # check each item in the dict
    for package in lock_data.get("package", []):

        # take the current package 
        package_data = {
            "name": package.get("name"),
            "version": package.get("version"),
            "wheels": package.get("wheels", []),
            "sdist": package.get("sdist")
        }

        # append to the dependencies list
        dependencies.append(package_data)
        dependencies_set.add(f"{package.get("name")}@{package.get("version")}")

    return dependencies , dependencies_set


def gather_npm_dependencies_from_locks(lock_files):
    """
        The function takes a list of npm lock files and gather all of
        the dependencies into a list and set
    """
    
    npm_dependencies = []
    npm_set = set()
    
    # gather the dependencies for each npm lockfile
    for lock_file in lock_files:
    
        # print message and extract dependencies
        print(f"Processing npm: {lock_file}")
        dependencies, dependencies_set = extract_npm_dependencies(lock_file)
        
        # add the dependencies to the set and list
        npm_dependencies.extend(dependencies)
        npm_set.update(dependencies_set)
        
    return npm_dependencies, npm_set


def gather_uv_dependencies_from_lockfiles(lock_files):
    """
        The function takes a list of uv lock files and gather all of
        the dependencies into a list and set
    """
    
    uv_dependencies = []
    uv_set = set()
    
    for lock_file in lock_files:
        
        # print message and extract dependencies
        print(f"Processing uv: {lock_file}")
        dependencies, dependencies_set = extract_uv_dependencies(lock_file)
        
        # add the dependencies to the set and list
        uv_dependencies.extend(dependencies)
        uv_set.update(dependencies_set)
        
    return uv_dependencies, uv_set
