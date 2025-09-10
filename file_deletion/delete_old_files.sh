
#!/bin/bash

# Directory to search
base_dir="/home/lamisplus/server/temp"

# Loop through each subdirectory in the base directory
for dir in "$base_dir"/*/; do
  if [ -d "$dir" ]; then
    echo "Processing directory: $dir"

    # Navigate to the subdirectory
    cd "$dir" || continue

    # Run the find commands to delete files
    find . -type f -name '*202501*' -exec rm {} +
    find . -type f -name '*202502*' -exec rm {} +
    find . -type f -name '*202503*' -exec rm {} +
    find . -type f -name '*202504*' -exec rm {} +
    find . -type f -name '*202505*' -exec rm {} +
    find . -type f -name '*202506*' -exec rm {} +
    find . -type f -name '*202507*' -exec rm {} +
    find . -type f -name '*202408*' -exec rm {} +
    find . -type f -name '*202409*' -exec rm {} +
    find . -type f -name '*202410*' -exec rm {} +
    find . -type f -name '*202411*' -exec rm {} +
    find . -type f -name '*202412*' -exec rm {} +

    # Return to the base directory
    cd "$base_dir" || exit
  fi
done
