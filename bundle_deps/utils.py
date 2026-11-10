import os
import shutil
import stat
import time
import tempfile
from functools import wraps
from contextlib import contextmanager


def runtime_count(func):
    @wraps(func)
    def count(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Total time: {end_time - start_time:.2f} seconds")
        return result
    return count


def remove_readonly(func, path, exc):
    """
        The function helps removing a full dir
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


@contextmanager
def temporary_directory():
    """
        The function yields a temporary directory that is always removed on exit,
        even when it holds read only files
    """

    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        shutil.rmtree(path, onexc=remove_readonly)


def validate_project_path(project_path):
    """
        The function validates the path of the project for export 
    """
    
    # checks if the path exists 
    if not os.path.exists(project_path):
        raise FileNotFoundError(f"Path does not exist: {project_path}")

    # checks if the path is not a dir
    if not os.path.isdir(project_path):
        raise NotADirectoryError(f"Path is not a directory: {project_path}")

    return project_path
