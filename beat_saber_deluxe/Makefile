TARGET := beat_saber_deluxe.prx

LIBS := -lGoldHEN_Hook -lSceLibcInternal -lkernel

TOOLCHAIN := $(OO_PS4_TOOLCHAIN)
INTDIR := obj
CRT := $(TOOLCHAIN)/lib/crtprx.o

CFILES := $(wildcard src/*.c)
# Exclude crt_patch.cpp — it conflicts with GoldHEN SDK's crtprx.o
CPPFILES := $(filter-out src/crt_patch.cpp src/hooks.cpp src/main_printf_backup.cpp, $(wildcard src/*.cpp))
OBJS := $(patsubst src/%.c, $(INTDIR)/%.o, $(CFILES)) $(patsubst src/%.cpp, $(INTDIR)/%.o, $(CPPFILES))

CFLAGS := --target=x86_64-pc-freebsd12-elf -fPIC -funwind-tables -c -isysroot $(TOOLCHAIN) -isystem $(TOOLCHAIN)/include -I./include
CXXFLAGS := $(CFLAGS) -isystem $(TOOLCHAIN)/include/c++/v1
LDFLAGS := -m elf_x86_64 -pie -e _init --script link.x --eh-frame-hdr -L$(TOOLCHAIN)/lib $(LIBS)

_unused := $(shell mkdir -p $(INTDIR))

UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
    CC := clang
    CCX := clang++
    LD := ld.lld
    CDIR := linux
endif
ifeq ($(UNAME_S),Darwin)
    CC := /usr/local/opt/llvm/bin/clang
    CCX := /usr/local/opt/llvm/bin/clang++
    LD := /usr/local/opt/llvm/bin/ld.lld
    CDIR := macos
endif

$(TARGET): $(OBJS) | $(INTDIR)
	$(LD) $(CRT) $(INTDIR)/*.o -o $(INTDIR)/beat_saber_deluxe.elf $(LDFLAGS)
	$(TOOLCHAIN)/bin/$(CDIR)/create-fself -in=$(INTDIR)/beat_saber_deluxe.elf -out=$(INTDIR)/beat_saber_deluxe.oelf --lib=$(TARGET) --paid 0x3800000000000011
	# GoldHEN expects FSELF format (--lib output, SCE magic 4f 15 3d 1d),
	# NOT bare OELF signed ELF (which starts with ELF magic 7f 45 4c 46)

$(INTDIR)/%.o: src/%.c
	$(CC) $(CFLAGS) -o $@ $<

$(INTDIR)/%.o: src/%.cpp
	$(CCX) $(CXXFLAGS) -o $@ $<

.PHONY: clean
.DEFAULT_GOAL := all

all: $(TARGET)

clean:
	rm -f $(TARGET) $(INTDIR)/*.elf $(INTDIR)/*.oelf $(OBJS)
