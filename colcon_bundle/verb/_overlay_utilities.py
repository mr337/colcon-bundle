import os
import shutil
import stat
import tarfile

from colcon_bundle.verb import logger
from colcon_bundle.verb.utilities import \
    update_shebang
from jinja2 import \
    Environment, \
    FileSystemLoader, \
    select_autoescape


_CONTEXT_VAR_BASH = {'shell': 'bash'}
_CONTEXT_VAR_SH = {'shell': 'sh'}


def create_workspace_overlay(install_base: str,
                             workspace_staging_path: str,
                             overlay_path: str):
    """
    Create overlay from user's built workspace install directory.

    :param str install_base: Path to built workspace install directory
    :param str workspace_staging_path: Path to stage the overlay build at
    :param str overlay_path: Name of the overlay file (.tar.gz)
    """
    workspace_install_path = os.path.join(
        workspace_staging_path, 'opt', 'built_workspace')
    shutil.rmtree(workspace_staging_path, ignore_errors=True)
    assets_directory = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'assets')

    shellscript_path = os.path.join(
        assets_directory,
        'v2_workspace_setup.sh'
    )
    shellscript_dest = os.path.join(workspace_staging_path, 'setup.sh')

    shellscript_path_bash = os.path.join(
        assets_directory,
        'v2_workspace_setup.bash'
    )
    shellscript_dest_bash = os.path.join(workspace_staging_path, 'setup.bash')

    # install_base: Directory with built artifacts from the workspace
    os.mkdir(workspace_staging_path)
    shutil.copy2(shellscript_path, shellscript_dest)
    os.chmod(shellscript_dest, 0o755)
    
    _generate_template(
        os.path.join(dep_staging_path, 'setup.sh'),
        _CONTEXT_VAR_SH
    )

    shutil.copy2(shellscript_path_bash, shellscript_dest_bash)
    os.chmod(shellscript_dest_bash, 0o755)
    
    _generate_template(
        os.path.join(dep_staging_path, 'setup.bash'),
        _CONTEXT_VAR_BASH
    )

    shutil.copytree(install_base, workspace_install_path)

    # This is required because python3 shell scripts use a hard
    # coded shebang
    update_shebang(workspace_staging_path)

    recursive_tar_gz_in_path(overlay_path,
                             workspace_staging_path)


def create_dependencies_overlay(staging_path, overlay_path):
    """
    Create the dependencies overlay from staging_path.

    :param str staging_path: Path where all the dependencies
    have been installed/extracted to
    :param str overlay_path: Path of overlay output file
    (.tar.gz)
    """
    dep_staging_path = staging_path
    dep_tar_gz_path = overlay_path
    logger.info('Dependencies changed, updating {}'.format(
        dep_tar_gz_path
    ))

    assets_directory = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'assets')

    shellscript_path = os.path.join(assets_directory, 'v2_setup.sh')
    shellscript_dest = os.path.join(dep_staging_path, 'setup.sh')

    shellscript_path_bash = os.path.join(
        assets_directory,
        'v2_setup.bash'
    )
    shellscript_dest_bash = os.path.join(dep_staging_path, 'setup.bash')

    shutil.copy2(shellscript_path, shellscript_dest)
    os.chmod(shellscript_dest, 0o755)
    
    _generate_template(shellscript_dest, _CONTEXT_VAR_SH)

    shutil.copy2(shellscript_path_bash, shellscript_dest_bash)
    os.chmod(shellscript_dest_bash, 0o755)
    
    _generate_template(shellscript_dest_bash, _CONTEXT_VAR_BASH)

    if os.path.exists(dep_tar_gz_path):
        os.remove(dep_tar_gz_path)
    recursive_tar_gz_in_path(dep_tar_gz_path,
                             dep_staging_path)


def recursive_tar_gz_in_path(output_path, path):
    """
    Create a tar.gz archive of all files inside a directory.

    This function includes all sub-folders of path in the root of the tarfile

    :param output_path: Name of archive file to create
    :param path: path to recursively collect all files and include in
    tar.gz. These will be included with path as the root of the archive.
    """
    with tarfile.open(output_path, mode='w:gz', compresslevel=5) as tar:
        logger.info(
            'Creating tar of {path}'.format(path=path))
        for name in os.listdir(path):
            some_path = os.path.join(path, name)
            tar.add(some_path, arcname=os.path.basename(some_path))


def _generate_template_new(dest, context_vars):
    with open(dest, 'w') as file:
        file.write(template.render(context_vars))
    os.chmod(dest, os.stat(dest).st_mode | stat.S_IEXEC)


def _generate_template(template_name, script_name, context_vars):
    """
    Generate setup.bash or setup.sh files from a template.
    This assumes the template is in the assets folder.
    :param template_name: Name of the template to be used
    :param script_name: name of the script to be generated
    :param context_vars: dictionary of values to be used for the variables in
    the template
    """
    template_location = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'assets/')
    env = Environment(
        autoescape=select_autoescape(['html', 'xml']),
        loader=FileSystemLoader(template_location),
        keep_trailing_newline=True,
    )

    template = env.get_template(template_name)

    script_location = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'assets/', script_name)

    with open(script_location, 'w') as file:
        file.write(template.render(context_vars))
    os.chmod(script_location, os.stat(script_location).st_mode | stat.S_IEXEC)

