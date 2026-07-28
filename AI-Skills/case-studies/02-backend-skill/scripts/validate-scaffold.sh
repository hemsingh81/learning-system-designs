#!/bin/bash
# scripts/validate-scaffold.sh
# Checks that a newly scaffolded endpoint has all four required
# layers. Takes the endpoint name as an argument.
#
# Usage: ./validate-scaffold.sh <endpoint-name>
# Example: ./validate-scaffold.sh getUserById

NAME=$1

if [ -z "$NAME" ]; then
  echo "Usage: validate-scaffold.sh <endpoint-name>"
  exit 2
fi

MISSING=()

[ -f "src/routes/${NAME}.ts" ]       || MISSING+=("route (src/routes/${NAME}.ts)")
[ -f "src/services/${NAME}.ts" ]     || MISSING+=("service (src/services/${NAME}.ts)")
[ -f "src/repositories/${NAME}.ts" ] || MISSING+=("repository (src/repositories/${NAME}.ts)")
[ -f "tests/${NAME}.test.ts" ]       || MISSING+=("test (tests/${NAME}.test.ts)")

if [ ${#MISSING[@]} -eq 0 ]; then
  echo "All 4 layers present for '${NAME}'."
  exit 0
else
  echo "Missing layers for '${NAME}':"
  printf '  - %s\n' "${MISSING[@]}"
  exit 1
fi
