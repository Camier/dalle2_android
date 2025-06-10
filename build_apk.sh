#!/bin/bash
source venv/bin/activate
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3
buildozer android debug
