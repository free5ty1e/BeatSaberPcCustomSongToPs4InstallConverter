// Beat Saber Deluxe v0.09 — Manual hooks via sys_sdk_proc_rw + klog
// BOTH fopen and open hooks installed via GoldHEN kernel write (no mprotect).
// Logging via klog (sys_sdk_cmd KLOG) — no file I/O, no crash.
// Stubs allocated via sceKernelMmap with jb fixed.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.09"

// --- Global state ---
static int in_hook = 0;
static void *fopen_stub = NULL;
static void *open_stub = NULL;
static int stub_size = 14 + 14;  // saved bytes (14) + jump back (14)

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

// --- klog logging (via GoldHEN syscall — no file I/O) ---
static void klog_msg(const char *msg) {
    sys_sdk_cmd(GOLDHEN_SDK_CMD_KLOG, (void*)msg);
}

// --- Memory write via GoldHEN kernel access (no mprotect needed) ---
static void mem_write(uint64_t addr, void *data, uint64_t len) {
    struct proc_rw rw;
    memset(&rw, 0, sizeof(rw));
    rw.address = addr; rw.data = data; rw.length = len; rw.write_flags = 1;
    sys_sdk_proc_rw(&rw);
}
static void mem_read(uint64_t addr, void *data, uint64_t len) {
    struct proc_rw rw;
    memset(&rw, 0, sizeof(rw));
    rw.address = addr; rw.data = data; rw.length = len; rw.write_flags = 0;
    sys_sdk_proc_rw(&rw);
}

// --- Stub creation: saved bytes + jb fix + jump back ---
static void *create_stub(void *target, int fix_jb) {
    uint8_t saved[14];
    mem_read((uint64_t)target, saved, 14);

    if (fix_jb) {
        // Fix PC-relative jb/jne/je to nop;nop
        for (int i = 0; i < 13; i++) {
            if (saved[i] == 0x72 || saved[i] == 0x74 || saved[i] == 0x75) {
                saved[i] = 0x90; saved[i+1] = 0x90;
                break;
            }
        }
    }

    void *stub = NULL;
    int res = sceKernelMmap(0, stub_size, VM_PROT_ALL, 0x1000 | 0x2, -1, 0, &stub);
    if (res != 0 || !stub) return NULL;

    memcpy(stub, saved, 14);
    // Write jmp [rip+0] → target+14 after saved bytes
    uint8_t jmp_back[14] = {0xFF,0x25,0,0,0,0,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90};
    int32_t off = (int64_t)((uint8_t*)target + 14) - (int64_t)((uint8_t*)stub + 14 + 6);
    memcpy(jmp_back + 2, &off, 4);
    memcpy((uint8_t*)stub + 14, jmp_back, 14);
    return stub;
}

// --- Jump installation via sys_sdk_proc_rw ---
static void install_jump(void *target, void *hook_func) {
    uint8_t jump[12] = {0x48,0xB8,0,0,0,0,0,0,0,0,0xFF,0xE0};
    *(uint64_t*)&jump[2] = (uint64_t)hook_func;
    mem_write((uint64_t)target, jump, 12);
}

// --- Redirect logic ---
static const char* redirect_path(const char* path) {
    if (!path) return NULL;
    if (strstr(path, "startmeup") || strstr(path, "StartMeUp") || strstr(path, "start_me_up"))
        return "/data/custom/bs_deluxe/CustomSong";
    return NULL;
}

// --- fopen hook ---
typedef FILE *(*fopen_t)(const char*, const char*);
static FILE *fopen_hook(const char *path, const char *mode) {
    if (in_hook) return ((fopen_t)fopen_stub)(path, mode);
    in_hook = 1;
    const char *safe = path ? path : "NULL";
    const char *np = redirect_path(path);
    FILE *r;
    if (np) {
        char buf[128]; snprintf(buf, sizeof(buf), "REDIR fopen: %s", safe); klog_msg(buf);
        r = ((fopen_t)fopen_stub)(np, mode);
    } else {
        r = ((fopen_t)fopen_stub)(path, mode);
    }
    in_hook = 0;
    return r;
}

// --- open hook ---
typedef int (*open_t)(const char*, int, int);
static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return ((open_t)open_stub)(path, flags, 0);
    in_hook = 1;
    const char *safe = path ? path : "NULL";
    const char *np = redirect_path(path);
    int r;
    if (np) {
        char buf[128]; snprintf(buf, sizeof(buf), "REDIR open: %s", safe); klog_msg(buf);
        r = ((open_t)open_stub)(np, flags, 0);
    } else {
        r = ((open_t)open_stub)(path, flags, 0);
    }
    in_hook = 0;
    return r;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc; (void)args;
    OrbisNotificationRequest req;

    // 1. Startup notification
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "BS Deluxe %s", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // 2. Jailbreak for process-wide access
    struct jailbreak_backup jb;
    memset(&jb, 0, sizeof(jb));
    int jr = sys_sdk_jailbreak(&jb);
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "JB %s", jr == 0 ? "OK" : "FAIL");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // 3. Create stubs (read original bytes, fix jb for open, allocate exec memory)
    fopen_stub = create_stub((void*)&fopen, 0);  // fopen is long - no jb fix needed
    open_stub = create_stub((void*)&open, 1);   // open is short - fix jb

    // 4. Install jumps via sys_sdk_proc_rw (kernel write, no mprotect)
    if (fopen_stub) install_jump((void*)&fopen, (void*)fopen_hook);
    if (open_stub) install_jump((void*)&open, (void*)open_hook);

    // 5. Result notification
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "fopen=%s open=%s",
             fopen_stub ? "OK" : "FAIL", open_stub ? "OK" : "FAIL");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    klog_msg("BS Deluxe v0.09 started");
    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc; (void)args;
    if (fopen_stub) sceKernelMunmap(fopen_stub, stub_size);
    if (open_stub) sceKernelMunmap(open_stub, stub_size);
    return 0;
}
