from pathlib import Path

from clld.web.assets import environment

import gramfinder


environment.append_path(
    Path(gramfinder.__file__).parent.joinpath('static').as_posix(),
    url='/gramfinder:static/')
environment.load_path = list(reversed(environment.load_path))
