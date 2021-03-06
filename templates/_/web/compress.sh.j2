#!/usr/bin/env bash

FILES=$(find -type f -not -name '*.gz')

for file in ${FILES}; do
  file_gzipped="$file.gz"

  gzip -6 --no-name --stdout "$file" > "$file_gzipped"

  before=$(stat -c%s "$file")
  after=$(stat -c%s "$file_gzipped")
  if [[ "$after" -ge "$before" ]]; then
    rm "$file_gzipped"
  fi
done
