export HUMAN_DATETIMES_LOG_LEVEL=DEBUG

in_venv() {
    if python -c 'import sys; sys.exit(1 if sys.prefix == sys.base_prefix else 0)'; then
        "$@"
    else
        poetry run -- "$@"
    fi
}

test() {
    in_venv pytest -vv "$@"
}

run() {
    in_venv human-datetimes "$@"
}

update() {
    poetry show --latest --top-level
}

go() {
    run sandbox
}
