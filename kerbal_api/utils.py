import os


KSP_INSTALL_PATH_ENV_VAR_NAME = "KSP_INSTALL_PATH"


def get_ksp_install_path() -> str:
    """Return the configured Kerbal Space Program installation path."""
    install_path = os.getenv(KSP_INSTALL_PATH_ENV_VAR_NAME, None)
    if install_path is not None:
        return install_path

    common_windows_install_path = (
        "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Kerbal Space Program\\"
    )
    if os.path.isdir(common_windows_install_path):
        return common_windows_install_path

    common_windows_wsl_install_path = (
        "/mnt/c/Program Files (x86)/Steam/steamapps/common/Kerbal Space Program/"
    )
    if os.path.isdir(common_windows_wsl_install_path):
        return common_windows_wsl_install_path

    raise ValueError(
        f"Unable to find a Kerbal Space Program installation after looking at common paths. "
        f"Please set the {KSP_INSTALL_PATH_ENV_VAR_NAME} env var to the absolute path of "
        f"the KSP root directory (the one that contains the GameData directory)."
    )
