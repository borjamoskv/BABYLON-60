.PHONY: build install uninstall clean

PREFIX ?= /usr/local
BINARY = ramguard

build:
	swift build -c release
	@echo "✓ Built .build/release/$(BINARY)"

install: build
	install -d $(PREFIX)/bin
	install .build/release/$(BINARY) $(PREFIX)/bin/$(BINARY)
	@echo "✓ Installed to $(PREFIX)/bin/$(BINARY)"
	$(PREFIX)/bin/$(BINARY) install

uninstall:
	$(PREFIX)/bin/$(BINARY) uninstall 2>/dev/null || true
	rm -f $(PREFIX)/bin/$(BINARY)
	@echo "✓ Uninstalled"

clean:
	swift package clean
	rm -rf .build
