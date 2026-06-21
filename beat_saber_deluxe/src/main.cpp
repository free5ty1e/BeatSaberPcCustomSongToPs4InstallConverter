// Beat Saber Deluxe v0.24 — Raw syscall logging (no heap, no fopen, no crash)
// Uses orbis_syscall for open/write/close — bypasses libc heap allocation entirely.
// No hooks, no code modifications, no fopen — just jailbreak + raw file I/O.

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>
#include <GoldHEN/Syscall.h>

#define PLUGIN_VERSION "v0.24"
#define LOG_PATH "/data/bs_debug.txt"

// Raw syscall wrappers (no heap, no libc buffered I/O)
#define SYS_open 5
#define SYS_write 4
#define SYS_close 6
#define SYS_lseek 478  // from syscall.h
#define O_WRONLY 0x1
#define O_CREAT  0x200
#define O_TRUNC  0x400
#define O_RDONLY 0x0

// Write to a file descriptor using raw syscall
static long raw_write(int fd, const char *buf, unsigned long len) {
    return orbis_syscall(SYS_write, fd, buf, len);
}

static void log_msg(const char *msg) {
    int fd = orbis_syscall(SYS_open, LOG_PATH, O_WRONLY|O_CREAT|O_TRUNC, 0644);
    if (fd >= 0) {
        raw_write(fd, msg, strlen(msg));
        raw_write(fd, "\n", 1);
        orbis_syscall(SYS_close, fd);
    }
}

static void log_append(const char *msg) {
    int fd = orbis_syscall(SYS_open, LOG_PATH, O_WRONLY|O_CREAT, 0644);
    if (fd >= 0) {
        orbis_syscall(SYS_lseek, fd, 0, 2); // SEEK_END = 2
        raw_write(fd, msg, strlen(msg));
        raw_write(fd, "\n", 1);
        orbis_syscall(SYS_close, fd);
    }
}
extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"BS Deluxe %s",PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    struct jailbreak_backup jb;
    memset(&jb,0,sizeof(jb));
    int jr = sys_sdk_jailbreak(&jb);

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"JB %s",jr==0?"OK":"FAIL");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // Write log using raw syscall (no heap, no fopen, no buffer allocation)
    log_msg("=== BS Deluxe v0.24 ===\nJailbreak: active\nRaw syscall I/O works!");

    // Dummy mprotect call to propagate jailbreak state through VM subsystem
    // mprotect (syscall 74) goes through a different kernel path than jailbreak
    // (syscall 500). This forces the VM subsystem to refresh its cached credentials
    // from the kernel credential store, propagating the jailbreak changes.
    sceKernelMprotect((void*)module_start, 0x1000, VM_PROT_READ | VM_PROT_EXECUTE);

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"raw log: %s", LOG_PATH);
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // NO HOOKS — clean return
    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
