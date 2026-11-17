#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
TARGET="${CARGO_TARGET_DIR:-target}"
# A matching CLI is required for wasm-bindgen's generated JavaScript ABI.
VERSION=$(awk '/^name = "wasm-bindgen"$/ { found=1; next } found && /^version = / { gsub(/"/, "", $3); print $3; exit }' Cargo.lock)
if ! command -v wasm-bindgen >/dev/null 2>&1 || [ "$(wasm-bindgen --version)" != "wasm-bindgen $VERSION" ]; then
    echo "Install the matching CLI: cargo install wasm-bindgen-cli --version $VERSION --locked" >&2
    exit 1
fi
cargo build --release --locked --target wasm32-unknown-unknown --bin screech
mkdir -p dist/pkg
wasm-bindgen --target web --no-typescript --out-dir dist/pkg "$TARGET/wasm32-unknown-unknown/release/screech.wasm"
cp web/index.html web/boot.mjs dist/
touch dist/.nojekyll
printf '%s\n' 'Web build: dist/ (serve over HTTP; see README.md)'
