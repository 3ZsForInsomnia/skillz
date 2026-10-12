# skillz

Download, track, and organize agent skills in a namespaced local library.

- Namespaces are folders in the library. Downloaded skills default to `vendor/<owner>/<skill>`.
- `skillz.lock.json` (at the library root) records where each downloaded skill came from and
  the hashes needed to detect local edits and upstream updates.
- `skillz.toml` (in `$XDG_CONFIG_HOME/skillz/`) holds user settings: the library location and
  per-namespace options.

Requires Python 3.11+ and `git`. No third-party dependencies.

## Development

```sh
uv run python -m unittest discover -s tests
```
