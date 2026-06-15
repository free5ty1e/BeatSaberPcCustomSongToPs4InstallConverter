// Beat Saber Deluxe — POSIX file write test (open/write/close)
// Tests if low-level file I/O works during module_start
// fopen/fprintf crashes — let's try open/write/close instead

#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <orbis/libkernel.h>

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Show notification
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    strcpy(req.message, "BS Deluxe: Plugin Loaded!");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Try writing to USB using POSIX open/write/close
    // This bypasses libc's FILE* layer (fopen) which might cause the crash
    const char* paths[] = {
        "/mnt/usb0/bs_deluxe.log",
        "/data/bs_deluxe.log",
        "/tmp/bs_deluxe.log",
        NULL
    };

    for (int i = 0; paths[i]; i++) {
        int fd = open(paths[i], O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd >= 0) {
            write(fd, "BS Deluxe: plugin loaded successfully!\n", 39);
            write(fd, "Format: FSELF\n", 14);
            write(fd, "module_start ran OK\n", 20);
            close(fd);
        }
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
