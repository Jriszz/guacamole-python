"Extensions module. Each extension is initialized in the app factory located in app.py."
from flask_caching import Cache


cache = Cache(config={"CACHE_TYPE": "FileSystemCache", "CACHE_DIR": "file_dir"})
