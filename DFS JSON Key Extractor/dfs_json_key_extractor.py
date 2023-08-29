import json
import argparse
import re
from collections import defaultdict
import re

def truncate_key_patterns(key_path):
    """
    Truncate specific repetitive patterns in the key paths for better visualization.
    """
    # Truncate patterns like response_1_form_field, response_2_form_field to response_{1-5}_form_field
    pattern = re.compile(r'response_\d+_form_field')
    if re.search(pattern, key_path):
        indices = sorted(list(set(map(int, re.findall(r'response_(\d+)_form_field', key_path)))))
        if len(indices) == 1:
            return key_path  # If there's only one unique index, don't modify the key path
        return re.sub(pattern, f'response_{{{indices[0]}-{indices[-1]}}}_form_field', key_path)
    
    return key_path

def is_pattern(key):
    """Check if a key is a regular expression pattern."""
    return key.startswith('/') and key.endswith('/')

def match_pattern(pattern, key):
    """Try to match a regular expression pattern with a key."""
    return re.match(pattern[1:-1], key)

def extract_key_from_dict(data, key, path=[]):
    """
    Recursively search for occurrences of a key or pattern within a dictionary and 
    yield their paths.
    """
    for k, v in data.items():
        new_path = path + [k]
        if is_pattern(key):
            if match_pattern(key, k):
                yield tuple(new_path)
        else:
            if k == key:
                yield tuple(new_path)
        yield from extract_key_paths(v, key, new_path)

def extract_key_from_list(data, key, path=[]):
    """
    Recursively search for occurrences of a key or pattern within a list and 
    yield their paths.
    """
    for idx, item in enumerate(data):
        new_path = path + ['*']
        yield from extract_key_paths(item, key, new_path)

def extract_key_paths(data, key, path=[]):
    """
    Entry function to start the recursive search for key paths.
    """
    if isinstance(data, dict):
        yield from extract_key_from_dict(data, key, path)
    elif isinstance(data, list):
        yield from extract_key_from_list(data, key, path)

def increment_path_count(path_counts, path):
    """
    Increment the count of a given path.
    """
    path_counts[path] += 1

def gather_path_counts(paths):
    """
    Count occurrences of each path.
    """
    path_counts = defaultdict(int)
    for path in paths:
        increment_path_count(path_counts, path)
    return path_counts

def check_and_append_to_list(path, count, list_to_append):
    """
    Append path to a list if it meets the criteria.
    """
    if count > 1:
        list_to_append.append(path)

def separate_common_and_unique_paths(path_counts):
    """
    Separate paths into two lists: common paths and unique paths.
    """
    common_paths = []
    unique_paths = []

    for path, count in path_counts.items():
        if count == 1:
            unique_paths.append(path)
        else:
            check_and_append_to_list(path, count, common_paths)

    return common_paths, unique_paths

def print_path(path):
    """
    Print a single path with the appropriate indentation.
    """
    truncated_path = truncate_key_patterns('.'.join(path))
    indentation_level = len(path) - 1
    print('\t' * indentation_level + truncated_path)

def print_paths(paths, description):
    """
    Print all paths under a given description.
    """
    print(description)
    for path in paths:
        print_path(path)

def display_paths(file_path, keys):
    """
    Main function to extract and display paths for given keys in a JSON file.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    for key in keys:
        paths = list(extract_key_paths(data, key))
        
        path_counts = gather_path_counts(paths)
        common_paths, unique_paths = separate_common_and_unique_paths(path_counts)
        
        print(f"\nResults for key: {key}")
        print("-------------------------------")
        print_paths(common_paths, "Common paths:")
        
        if unique_paths:
            print("\n")
            print_paths(unique_paths, "Unique or specific paths (with their indices):")

def extract_variable_part(pattern, string):
    """ Extract the variable part of the string according to the pattern """
    match = re.search(pattern, string)
    if match:
        return match.group(1)
    return None

def find_repetitive_patterns(endings):
    """ Find patterns in the endings """
    pattern_candidates = [
        (re.compile(r'(.*)_(\d+)(_.*)'), int),  # For detecting numbers
        (re.compile(r'(.*)_(\w+)(_.*)'), str)  # For detecting strings
    ]

    for pattern, type_cast in pattern_candidates:
        variable_parts = [extract_variable_part(pattern, e) for e in endings]
        
        if None not in variable_parts:
            return pattern, [type_cast(vp) for vp in variable_parts]
    return None, []

def truncate_endings(endings):
    """ Truncate endings if there's a repetitive pattern """
    pattern, variable_parts = find_repetitive_patterns(endings)
    
    if not pattern:
        return endings  # Return as it is if no pattern found
    
    # Construct the truncated ending
    prefix, _, suffix = pattern.groups()
    
    if all(isinstance(vp, int) for vp in variable_parts):
        variable_parts.sort()
        truncated_ending = f"{prefix}_{{{variable_parts[0]}-{variable_parts[-1]}}}{suffix}"
        return [truncated_ending]
    else:
        truncated_ending = f"{prefix}_{'|'.join(variable_parts)}{suffix}"
        return [truncated_ending]

def combine_paths(base_dict):
    """ Combine paths by identifying repetitive patterns """
    combined_paths = []
    for base, endings in base_dict.items():
        combined_endings = truncate_endings(endings)
        for e in combined_endings:
            combined_paths.append(base + (e,))
    return combined_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and display paths for given keys in a JSON file.")
    parser.add_argument("file_path", type=str, help="Path to the JSON file.")
    parser.add_argument("keys", type=str, nargs='+', help="Keys to search for in the JSON file.")
    args = parser.parse_args()

    display_paths(args.file_path, args.keys)
