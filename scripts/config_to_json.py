#!/usr/bin/env python3
import sys
try:
  import tomli
except ImportError:
  try:
    import tomlkit as tomli
  except ImportError:
    sys.exit(7)

from pathlib import Path
try:
  with open(Path(Path.home(), ".config.toml"), 'rt') as f:
    data = tomli.load(f)
except FileNotFoundError:
  sys.exit(3)

import json
import tempfile
with tempfile.NamedTemporaryFile(suffix='.json', prefix='shell-config', delete=False, mode='w+t') as f:
  json.dump(data, f)
  print(f.name)
