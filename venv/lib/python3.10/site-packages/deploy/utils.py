import math
import os
import hashlib
import ast
from glob import glob
import subprocess


def get_checksum(file_path) -> str:
    """
    Get the MD5 checksum of a file, useful for determining if a file has changed on disk

    Args:
        file_path: The path of the file

    Returns:
        The checksum of the file

    """
    return hashlib.md5(open(file_path, "rb").read()).hexdigest()


def get_available_modules(src_directory):
    """Scan a directory for all python files and return a dictionary relating their module names to their absolute filepaths"""
    available_modules = {}
    for file in glob(os.path.join(src_directory, "*.py")):
        available_modules[os.path.basename(file.split(os.sep)[-1].split(".")[0])] = os.path.abspath(file)
    return available_modules


class RemovableDisk:
    path: str
    name: str

    def __init__(self, path, name):
        self.path = path
        self.name = name


def get_removable_disks(posix_mount_point_dir) -> list[RemovableDisk]:
    removable_drives = []

    if os.name == "nt":
        import psutil, win32api
        disks = psutil.disk_partitions()
        for disk in disks:
            if disk.fstype:
                removable_drives.append(RemovableDisk(win32api.GetVolumeInformation(disk.device)[0],disk.mountpoint))

    elif os.name == "posix":
        mount_points = os.listdir(posix_mount_point_dir)
        for mount_point in mount_points:
            drive_name = os.path.basename(mount_point)
            disk_path = os.path.abspath(os.path.join(os.path.join(posix_mount_point_dir, mount_point)))
            removable_drives.append(RemovableDisk(disk_path, drive_name))

    return removable_drives


def detect_dependencies(src_directory, file_path, available_libraries, ignored_imports, visited=None):
    """
    Find the dependencies of a python file recursively (all dependencies must be in src_directory)

    Args:
        src_directory: The directory where the source files are located, all imports must be in this directory
        file_path: The initial file to detect dependencies of
        available_libraries: A dictionary relating the names of the available libraries to their paths, this helps the function to resolve the imports to their respective files
        visited: The set of previously visited files. This prevents infinite recursion and defaults to an empty set

    Returns:
        A set with the names of all required modules that are not in ignored_imports
    """

    if visited is None:
        visited = set()

    with open(file_path, "r") as file:
        file_content = file.read()

    tree = ast.parse(file_content)
    imported_modules = set()

    for node in ast.walk(tree):
        module_names = []
        if isinstance(node, ast.Import):
            module_names = [name.name for name in node.names]
        elif isinstance(node, ast.ImportFrom):
            module_names = [node.module]
        for module in module_names:
            if module not in visited and module.split(".")[0] not in ignored_imports:
                # Add the module to the visited set
                visited.add(module)
                # Add the module to the imported set
                imported_modules.add(module)
                # Ensure the imported module exists in
                if module not in available_libraries:
                    raise ModuleNotFoundError(
                        f"File {file_path} references module '{module}' but, it could not be found"
                    )
                # Recurse until no additional modules can be found
                imported_modules.update(
                    detect_dependencies(
                        src_directory, available_libraries[module], available_libraries, ignored_imports, visited
                    )
                )

    return imported_modules


def unmount_drive(drive_path):
    if os.name == "nt":
        eject_command = f"powershell $driveEject = New-Object -comObject Shell.Application;" \
                        f"$driveEject.Namespace(17).ParseName('''{drive_path}''').InvokeVerb('''Eject''')"
    else:
        eject_command = ["umount", drive_path]

    subprocess.run(eject_command, check=True)


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "ZB", "YB")
    i = int(math.floor((math.log(size_bytes, 1024))))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s}, {size_name[i]}"
