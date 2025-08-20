from pathlib import Path

from dynaconf import Dynaconf

CONFIG_FILES = [
    "src/configs/settings.yaml",
]

settings = Dynaconf(
    settings_files=[C for C in CONFIG_FILES if Path(C).is_file()],
    environments=True,
)
