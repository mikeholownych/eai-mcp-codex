import os

def find_missing_files(root_dir):
    all_files = set()
    for root, _, files in os.walk(root_dir):
        for file in files:
            all_files.add(os.path.join(root, file))

    missing_files = set()

    for filepath in all_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, IOError):
            continue

        # Simple split by quotes to find potential paths
        for quote in ['"', "'"]:
            parts = content.split(quote)
            for i in range(1, len(parts), 2):
                path = parts[i]
                if ' ' in path or '\n' in path or len(path) < 3:
                    continue

                if '/' not in path and '.' not in path:
                    continue

                # Resolve the absolute path
                if path.startswith('/'):
                    abs_path = os.path.join(root_dir, path.lstrip('/'))
                else:
                    abs_path = os.path.normpath(os.path.join(os.path.dirname(filepath), path))

                if not os.path.exists(abs_path):
                    missing_files.add((path, filepath))

    return missing_files

if __name__ == '__main__':
    missing = find_missing_files('.')
    if missing:
        print('Missing files found:')
        for path, found_in in missing:
            print(f'  - "{path}" referenced in "{found_in}"')
    else:
        print('No missing files found.')
