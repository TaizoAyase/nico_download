# nico_download

# What's this

- ニコニコ動画から検索して指定場所にdownloadするpython script
- depends on [nndownload](https://github.com/AlexAplin/nndownload)

# how to use

## installation

please use uv

```bash
$ uv sync
```

## edit config

- `cp config.toml.example config.toml`
- edit `config.toml` to pass the uid and password of niconico and queries

## run

```bash
$ uv run main.py --help  # to check flags
$ uv run main.py
```
