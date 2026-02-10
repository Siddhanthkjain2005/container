# KernelSight Runtime Makefile

CC = gcc
CFLAGS = -Wall -Wextra -fPIC -g -O2
LDFLAGS = -shared

SRC_DIR = src
INC_DIR = include
BUILD_DIR = build

SRCS = $(wildcard $(SRC_DIR)/*.c)
OBJS = $(SRCS:$(SRC_DIR)/%.c=$(BUILD_DIR)/%.o)

LIB_NAME = libminicontainer.so
CLI_NAME = kernelsight-runtime

.PHONY: all clean install lib cli

all: lib cli

lib: $(BUILD_DIR)/$(LIB_NAME)

$(BUILD_DIR)/$(LIB_NAME): $(OBJS)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(LDFLAGS) -o $@ $^

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c $(INC_DIR)/container.h
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(INC_DIR) -c -o $@ $<

cli: $(BUILD_DIR)/$(CLI_NAME)

$(BUILD_DIR)/$(CLI_NAME): cli/main.c $(BUILD_DIR)/$(LIB_NAME)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(INC_DIR) -o $@ $< -L$(BUILD_DIR) -lminicontainer -Wl,-rpath,'$$ORIGIN'

clean:
	rm -rf $(BUILD_DIR)

install: all
	install -d /usr/local/lib /usr/local/bin /usr/local/include/minicontainer
	install -m 644 $(BUILD_DIR)/$(LIB_NAME) /usr/local/lib/
	install -m 755 $(BUILD_DIR)/$(CLI_NAME) /usr/local/bin/
	install -m 644 $(INC_DIR)/*.h /usr/local/include/minicontainer/
	ldconfig

test: all
	@echo "Running basic tests..."
	sudo LD_LIBRARY_PATH=$(BUILD_DIR) $(BUILD_DIR)/$(CLI_NAME) --help
