import os
import tarfile


def create_bundle_archive(source_dir, output_file):
    """
        The function takes the directory that contains
        the dependencies and zip it into a bundle
    """
    try:
        # create a gz gile
        with tarfile.open(output_file, "w:gz") as tar:
            # add the dir 
            tar.add(source_dir, arcname=os.path.basename(source_dir))
    except (tarfile.TarError, OSError) as error:
        raise RuntimeError(
            f"Failed to create bundle archive: {source_dir}"
        ) from error


def create_dependencies_archive(source_dir, output_file):
    """
        The function creates an archive of every dependency
    """
    try:
        # create a new gz fie and add all of the files in the dir
        with tarfile.open(output_file, "w:gz") as tar:
            for file in os.listdir(source_dir):
                file_path = os.path.join(source_dir, file)
                tar.add(file_path, arcname=file)
    except (tarfile.TarError, OSError) as error:
        raise RuntimeError(
            f"Failed to create dependencies archive: {source_dir}"
        ) from error
        
    print(f"Dependencies archive created: {output_file}")
