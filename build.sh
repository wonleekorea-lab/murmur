#!/bin/sh
# core.html を正本に、index.html（PWA本体）と artifact.html（body相当）を生成する。
# 二重管理を避けるため、アプリのコードは core.html にだけ書くこと。
set -e
D=$(dirname "$0")

# 1. Artifact 用（<html>/<head>/<body> なしの素の本体）
cp "$D/core.html" "$D/artifact.html"

# 2. PWA 用（外殻を巻く。<title> は head 側に置いてあるので本体からは落とす）
{
  cat "$D/shell-head.html"
  grep -v '^<title>' "$D/core.html"
  cat "$D/shell-foot.html"
} > "$D/index.html"

echo "built: index.html artifact.html"
