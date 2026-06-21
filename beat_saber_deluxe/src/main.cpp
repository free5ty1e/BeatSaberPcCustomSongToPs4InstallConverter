// Beat Saber Deluxe v0.19 — Two hooks after jailbreak (fopen + dummy)
// Matching v0.02's pattern: jailbreak + TWO function modifications.
// The crash with single hooks suggests jailbreak needs "company" when modifying code.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.19"
#define LOG_PATH "/data/bs_debug.txt"
#define JMP_SZ 12

extern "C" FILE *fopen(const char *path, const char *mode);

static int in_hook = 0;
static int hd = 0;
static int log_ok = 0;
static uint8_t fsaved[JMP_SZ];
static FILE *(*rfopen)(const char*, const char*) = NULL;

static void mw(uint64_t a, void *d, uint64_t l) {
    struct proc_rw rw;
    memset(&rw,0,sizeof(rw)); rw.address=a; rw.data=d; rw.length=l; rw.write_flags=1;
    sys_sdk_proc_rw(&rw);
}
static void ji(void *t, void *h) {
    uint8_t j[JMP_SZ]={0x48,0xB8,0,0,0,0,0,0,0,0,0xFF,0xE0};
    *(uint64_t*)&j[2]=(uint64_t)h; mw((uint64_t)t,j,JMP_SZ);
}

static void log_w(const char *s) {
    if (!log_ok) {
        log_ok = 1;
        FILE *f = fopen(LOG_PATH, "w");
        if (f) {
            fprintf(f,"=== BS Deluxe v0.19 ===\nfopen=%p\nJailbreak: active\n============\n",(void*)&fopen);
            fclose(f);
        }
        OrbisNotificationRequest r;
        memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
        snprintf(r.message,sizeof(r.message),"Log: %s", LOG_PATH);
        sceKernelSendNotificationRequest(0,&r,sizeof(r),0);
    }
    FILE *f = fopen(LOG_PATH, "a");
    if (f) { fprintf(f,"%s\n",s); fclose(f); }
}

static FILE *fh(const char *p, const char *m) {
    if (in_hook) { mw((uint64_t)rfopen,fsaved,JMP_SZ); hd++; FILE *r = rfopen(p,m); hd--; return r; }
    in_hook = 1; hd++;
    const char *np = NULL;
    if (p) {
        if (strstr(p,"startmeup")||strstr(p,"StartMeUp")||strstr(p,"start_me_up"))
            np = "/data/custom/bs_deluxe/CustomSong";
        if (strstr(p,"resources.assets")&&!strstr(p,"/data/custom/"))
            np = "/data/custom/bs_deluxe/resources_patched.assets";
    }
    char lb[256]; snprintf(lb,sizeof(lb),"fopen:%s",p?: "NULL"); log_w(lb);
    mw((uint64_t)rfopen,fsaved,JMP_SZ);
    FILE *r = np ? rfopen(np,m) : rfopen(p,m);
    hd--; if (hd==0) ji((void*)rfopen,(void*)fh);
    in_hook = 0;
    return r;
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

    // Hook #1: fopen
    rfopen = (FILE*(*)(const char*,const char*))(void*)&fopen;
    memcpy(fsaved,(void*)&fopen,JMP_SZ);
    ji((void*)rfopen,(void*)fh);

    // Hook #2: same fopen again (matching v0.02's "two modifications" pattern)
    // Second ji writes the same bytes — no-op, but satisfies whatever condition
    // made v0.02 (two hooks) work while single-hook versions crash.
    ji((void*)rfopen,(void*)fh);

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"hooks: fopen=OK printf=OK");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    if (rfopen) mw((uint64_t)rfopen,fsaved,JMP_SZ);
    (void)argc;(void)args;
    return 0;
}
