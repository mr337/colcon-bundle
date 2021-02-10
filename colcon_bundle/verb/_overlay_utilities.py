import os
from pathlib import Path
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
                             ws_staging_path: str,
                             overlay_path: str):
    """
    Create overlay from user's built workspace install directory.

    :param str install_base: Path to built workspace install directory
    :param str ws_staging_path: Path to stage the overlay build at
    :param str overlay_path: Name of the overlay file (.tar.gz)
    """
    ws_install_path = Path(ws_staging_path) / 'opt' / 'built_workspace'

    shutil.rmtree(ws_staging_path, ignore_errors=True)

    shellscript_dest = Path(ws_staging_path) / 'setup.sh'
    shellscript_dest_bash = Path(ws_staging_path) / 'setup.bash'

    # install_base: Directory with built artifacts from the workspace
    os.mkdir(ws_staging_path)

    _rendering_template(
        'v2_workspace_setup.jinja2.sh',
        shellscript_dest,
        _CONTEXT_VAR_SH
    )
    shellscript_dest.chmod(0o755)

    _rendering_template(
        'v2_workspace_setup.jinja2.sh',
        shellscript_dest_bash,
        _CONTEXT_VAR_BASH
    )
    shellscript_dest_bash.chmod(0o755)

    shutil.copytree(install_base, str(ws_install_path))

    # This is required because python3 shell scripts use a hard
    # coded shebang
    update_shebang(ws_staging_path)

    recursive_tar_gz_in_path(overlay_path, ws_staging_path)


def create_dependencies_overlay(staging_path: str, overlay_path: str):
    """
    Create the dependencies overlay from staging_path.

    :param str staging_path: Path where all the dependencies
    have been installed/extracted to
    :param str overlay_path: Path of overlay output file
    (.tar.gz)
    """
    dep_staging_path = Path(staging_path)
    dep_tar_gz_path = Path(overlay_path)
    logger.info('Dependencies changed, updating {}'.format(
        str(dep_tar_gz_path)
    ))

    shellscript_dest = Path(dep_staging_path) / 'setup.sh'
    shellscript_dest_bash = Path(dep_staging_path) / 'setup.bash'

    _rendering_template(
        'v2_setup.jinja2.sh',
        shellscript_dest,
        _CONTEXT_VAR_SH
    )
    shellscript_dest.chmod(0o755)

    _rendering_template(
        'v2_setup.jinja2.sh',
        shellscript_dest_bash,
        _CONTEXT_VAR_BASH
    )
    shellscript_dest_bash.chmod(0o755)

    if dep_tar_gz_path.exists():
        dep_tar_gz_path.unlink()
    recursive_tar_gz_in_path(str(dep_tar_gz_path), str(dep_staging_path))


def recursive_tar_gz_in_path(output_path: str, path: str):
    """
    Create a tar.gz archive of all files inside a directory.

    This function includes all sub-folders of path in the root of the tarfile

    :param output_path: Name of archive file to create
    :param path: path to recursively collect all files and include in
    tar.gz. These will be included with path as the root of the archive.
    """
    p = Path(path)
    with tarfile.open(output_path, mode='w:gz', compresslevel=5) as tar:
        logger.info(
            'Creating tar of {path}'.format(path=path))
        for name in p.iterdir():
            some_path = Path(p) / name
            tar.add(str(some_path), arcname=os.path.basename(str(some_path)))


def _rendering_template(template_name: str,
                        script_dest: Path,
                        context_vars: dict):
    """
    Render setup.bash or setup.sh files from template.

    This assumes the template is in the assets folder.

    :param template_name: Name of the template to be used
    :param script_dest: path of the script to be rendered
    :param context_vars: dictionary of values to be used for the variables in
    the template
    """
    template_location = Path(__file__).parent.absolute() / 'assets/'
    env = Environment(
        autoescape=select_autoescape(['html', 'xml']),
        loader=FileSystemLoader(str(template_location)),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)

    with script_dest.open('w') as file:
        file.write(template.render(context_vars))
    script_dest.chmod(script_dest.stat().st_mode | stat.S_IEXEC)
