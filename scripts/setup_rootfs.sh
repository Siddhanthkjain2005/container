#!/bin/bash
ROOTFS="/tmp/alpine-rootfs"
echo "Creating rootfs at $ROOTFS..."
mkdir -p "$ROOTFS/bin" "$ROOTFS/lib" "$ROOTFS/lib64" "$ROOTFS/proc" "$ROOTFS/sys" "$ROOTFS/dev" "$ROOTFS/tmp"

# Find busybox
BUSYBOX=$(which busybox)
if [ -z "$BUSYBOX" ]; then
    echo "Error: busybox not found!"
    exit 1
fi

rm -f "$ROOTFS/bin/busybox"
cp "$BUSYBOX" "$ROOTFS/bin/busybox"
chmod +x "$ROOTFS/bin/busybox"

# Create symlinks for all busybox applets
for cmd in $("$ROOTFS/bin/busybox" --list); do
    if [ "$cmd" != "busybox" ]; then
        ln -sf busybox "$ROOTFS/bin/$cmd" 2>/dev/null
    fi
done

# Copy essential shared libraries for busybox if it's not static
# Check if it's dynamically linked
if ldd "$BUSYBOX" >/dev/null 2>&1; then
    LIBS=$(ldd "$BUSYBOX" | grep -o '/lib[^ ]*' | sort -u)
    for lib in $LIBS; do
        mkdir -p "$ROOTFS$(dirname "$lib")"
        cp "$lib" "$ROOTFS$lib" 2>/dev/null || true
    done
fi

# Create essential device nodes (mocked if not root)
if [ "$(id -u)" -eq 0 ]; then
    mknod -m 666 "$ROOTFS/dev/null" c 1 3 2>/dev/null || touch "$ROOTFS/dev/null"
    mknod -m 666 "$ROOTFS/dev/zero" c 1 5 2>/dev/null || touch "$ROOTFS/dev/zero"
else
    touch "$ROOTFS/dev/null" "$ROOTFS/dev/zero"
fi
chmod 666 "$ROOTFS/dev/null" "$ROOTFS/dev/zero"

echo "Rootfs setup complete at $ROOTFS"
ls -F "$ROOTFS/bin"
