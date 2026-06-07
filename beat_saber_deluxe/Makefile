CC = clang
CFLAGS = -I./include -Wall -O2 -fPIC
LDFLAGS = -shared -nostdlib

# These paths will be updated once the SDK is installed
ORBIS_SDK = /opt/openorbis
TARGET = build/beat_saber_deluxe.sprx

SRC = src/main.cpp
OBJ = $(SRC:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJ)
	@mkdir -p build
	$(CC) $(CFLAGS) $(LDFLAGS) -o $(TARGET) $(OBJ)

%.o: %.cpp
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)
