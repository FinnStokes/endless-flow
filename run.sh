#/bin/sh

cd "$( dirname "${BASH_SOURCE[0]}" )"
if command -v python2 >/dev/null 2>&1; then
    python2 src/main.py $@
else
    python src/main.py $@
fi
