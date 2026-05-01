# Makefile for Beat Saber Deluxe (BSDX) GoldHEN Plugin

# Toolchain paths (set environment variables or modify here)
OO_PS4_TOOLCHAIN ?= /opt/orbis-sdk
GOLDHEN_SDK ?= /opt/GoldHEN_SDK

# Compiler and flags
CC = $(OO_PS4_TOOLCHAIN)/orant/bin/orbis-gcc
CXX = $(OO_PS4_TOOLCHAIN)/orant/bin/orbis-g++
LD = $(OO_PS4_TOOLCHAIN)/orant/bin/orbis-gcc

CFLAGS = -Wall -O2 -std=c11 -fvisibility=hidden
CXXFLAGS = -Wall -O2 -std=c++11 -fvisibility=hidden

# Include paths
INCLUDES = -I$(OO_PS4_TOOLCHAIN)/orant/include \
           -I$(GOLDHEN_SDK)/include \
           -I./include

# Source files
SOURCES = source/main.c source/plugin_common.c

# Object files
OBJECTS = $(SOURCES:.c=.o)

# Output
OUTPUT = BSDX-Plugin.prx

# Linker flags
LDFLAGS = -L$(OO_PS4_TOOLCHAIN)/orant/lib \
          -L$(GOLDHEN_SDK)/lib \
          -lGoldHEN \
          -lorbis \
          -lSceSysmodule \
          -lScePad \
          -lm

# Targets
all: $(OUTPUT)

$(OUTPUT): $(OBJECTS)
	$(LD) $(OBJECTS) $(LDFLAGS) -o $@
	@echo "Built: $(OUTPUT)"

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(OUTPUT)

.PHONY: all clean