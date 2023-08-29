import sys
import json
from collections.abc import Mapping, Sequence

def summarize_key(key, value):
    if isinstance(value, Mapping):
        return f"{key} (dict, {len(value)} keys)"
    elif isinstance(value, Sequence) and not isinstance(value, str):
        return f"{key} (list, {len(value)} elements)"
    else:
        return f"{key} ({type(value).__name__})"

def traverse_json_tree(data, indent=0):
    if isinstance(data, Mapping):
        for key, value in data.items():
            print(' ' * indent + summarize_key(key, value))
            traverse_json_tree(value, indent + 2)
    elif isinstance(data, Sequence) and not isinstance(data, str):
        for i, value in enumerate(data):
            print(f' ' * indent + f'[Element {i}]:')
            traverse_json_tree(value, indent + 2)

def extract_json_tree(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)

    # process only the first element if it's a list
    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    traverse_json_tree(data)

if __name__ == '__main__':
    path = sys.argv[1]
    extract_json_tree(path)