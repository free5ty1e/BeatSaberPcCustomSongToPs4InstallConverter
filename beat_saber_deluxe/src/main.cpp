// Beat Saber Deluxe v0.27 — AFR test: write to /data/GoldHEN/AFR/ path
// NO jailbreak, NO hooks. Just sceKernelOpen + sceKernelWrite + sceKernelClose.
// If GoldHEN's AFR intercepts this write and allows it through sandbox = we have logging!
// If sandbox blocks it, no crash (sceKernelOpen returns -1, unlike fopen which crashes).

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.27"
#define AFR_LOG "/data/GoldHEN/AFR/CUSA12878/bs_log.txt"

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"BS Deluxe %s",PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // NO JAILBREAK. Let AFR handle the sandbox for /data/GoldHEN/AFR/CUSA12878/
    int fd = sceKernelOpen(AFR_LOG, O_WRONLY|O_CREAT|O_TRUNC, 0644);
    if (fd >= 0) {
        sceKernelWrite(fd, "BS Deluxe v0.27: AFR write OK!\n", 32);
        sceKernelClose(fd);
        memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
        snprintf(r.message,sizeof(r.message),"AFR: OK");
        sceKernelSendNotificationRequest(0,&r,sizeof(r),0);
    } else {
        memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
        snprintf(r.message,sizeof(r.message),"AFR: FAIL (fd=%d)", fd);
        sceKernelSendNotificationRequest(0,&r,sizeof(r),0);
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
