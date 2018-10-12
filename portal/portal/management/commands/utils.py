def sanitize_version(raw_version):
    if raw_version[0] == 'v':
        return raw_version[1:]
    elif raw_version.startswith('release/'):
        return raw_version[8:]

    return raw_version
