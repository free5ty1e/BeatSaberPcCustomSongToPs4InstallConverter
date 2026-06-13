BUILD_FOLDER := bin
OUTPUT_PRX   := test_plugin
TARGET       := $(BUILD_FOLDER)/$(OUTPUT_PRX)
TARGET_ELF   := $(BUILD_FOLDER)/$(OUTPUT_PRX)
O_FLAG       := -O3

# Libraries linked into the ELF.
LIBS := -lGoldHEN_Hook -lkernel -lSceLibcInternal -lSceSysmodule -lScePad

EXTRAFLAGS := -D__USE_KLOG__ -D__FINAL__=1

# Root vars
TOOLCHAIN     := $(OO_PS4_TOOLCHAIN)
GH_SDK        := $(GOLDHEN_SDK)
PROJDIR       := source
INTDIR        := build
INCLUDEDIR    := include

# Define objects to build
CFILES      := $(wildcard $(PROJDIR)/*.c)
OBJS        := $(patsubst $(PROJDIR)/%.c, $(INTDIR)/%.o, $(CFILES))

# Define final C/C++ flags
CFLAGS      := --target=x86_64-pc-freebsd12-elf -fPIC -funwind-tables -c $(EXTRAFLAGS) -isysroot $(TOOLCHAIN) -isystem $(TOOLCHAIN)/include -I$(GH_SDK)/include -I$(INCLUDEDIR) $(O_FLAG)
LDFLAGS     := -m elf_x86_64 -pie --script $(TOOLCHAIN)/link.x -e _init --eh-frame-hdr -L$(TOOLCHAIN)/lib -L$(GH_SDK) $(LIBS)

# Create directories
_unused     := $(shell mkdir -p $(INTDIR))
_unused     := $(shell mkdir -p $(BUILD_FOLDER))

# Check for linux vs macOS and account for clang/ld path
UNAME_S     := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
        CC      := clang
        CCX     := clang++
        LD      := ld.lld
        CDIR    := linux
endif
ifeq ($(UNAME_S),Darwin)
        CC      := /usr/local/opt/llvm/bin/clang
        CCX     := /usr/local/opt/llvm/bin/clang++
        LD      := /usr/local/opt/llvm/bin/ld.lld
        CDIR    := macos
endif

$(TARGET): $(INTDIR) $(OBJS)
	$(LD) $(GH_SDK)/build/crtprx.o $(INTDIR)/*.o -o $(TARGET_ELF).elf $(LDFLAGS)
	$(TOOLCHAIN)/bin/$(CDIR)/create-fself -in=$(TARGET_ELF).elf -out=$(TARGET_ELF).oelf --lib=$(TARGET).prx --paid 0x3800000000000011

$(INTDIR)/%.o: $(PROJDIR)/%.c
	$(CC) $(CFLAGS) -o $@ $<

.PHONY: clean
.DEFAULT_GOAL := all

all: $(TARGET)

clean:
	rm -rf $(BUILD_FOLDER) $(INTDIR) $(OBJS)
