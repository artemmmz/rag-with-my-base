from dataclasses import dataclass

from pathlib import Path


@dataclass
class GeneralSettings:
    ROOT_DIR: Path = Path(__file__).parent.parent.absolute()
