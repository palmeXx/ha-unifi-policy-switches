# Run the tests against different Home Assistant and aiounifi versions.
#
#   make test                                  defaults: PHCC=0.13.375 AIOUNIFI=96
#   make test PHCC=0.13.375 AIOUNIFI=96        HA pinned by the given phcc release
#   make smoke HA=2026.11.1 AIOUNIFI=98        import and filter check only
#   make test-ha2026.10 / make smoke-ha2026.11 shortcuts for the known versions
#   make versions                              HA pin of the newest phcc releases
#   make versions HA=2026.11.1                 aiounifi pin and matching phcc
#
# pytest-homeassistant-custom-component (phcc) pins one Home Assistant version,
# so `test` uses the HA version of the phcc release. HA= overrides it, which
# only works if phcc still matches that HA version. For HA versions without a
# phcc release, use `smoke`, it runs without phcc.
# Each version combination gets its own virtual environment.

PYTHON ?= python3.14
PHCC ?= 0.13.375
AIOUNIFI ?= 96
HA ?=

TEST_VENV = .venv-test-phcc$(PHCC)$(if $(HA),-ha$(HA))-aiounifi$(AIOUNIFI)
SMOKE_VENV = .venv-smoke-ha$(HA)-aiounifi$(AIOUNIFI)

.PHONY: help test smoke test-ha2026.10 smoke-ha2026.11 test-all versions clean

help:
	@sed -n '2,14s/^# \{0,1\}//p' Makefile

test: $(TEST_VENV)/.installed
	$(TEST_VENV)/bin/pytest $(PYTEST_ARGS)

smoke: $(SMOKE_VENV)/.installed
	$(SMOKE_VENV)/bin/python scripts/smoke_test.py

# Latest phcc release, pins Home Assistant 2026.10.4 with aiounifi 96
test-ha2026.10:
	$(MAKE) test PHCC=0.13.375 AIOUNIFI=96 HA=

# No phcc release for 2026.11 yet
smoke-ha2026.11:
	$(MAKE) smoke HA=2026.11.1 AIOUNIFI=98

test-all: test-ha2026.10 smoke-ha2026.11

# Standard library only, runs without a virtual environment
versions:
	$(PYTHON) -I scripts/versions.py $(if $(HA),--ha $(HA)) $(if $(COUNT),--count $(COUNT))

$(TEST_VENV)/.installed:
	$(PYTHON) -m venv $(TEST_VENV)
	$(TEST_VENV)/bin/pip install -q -U pip
	$(TEST_VENV)/bin/pip install -q \
		pytest-homeassistant-custom-component==$(PHCC) \
		aiounifi==$(AIOUNIFI) \
		$(if $(HA),homeassistant==$(HA))
	touch $@

$(SMOKE_VENV)/.installed:
	@test -n "$(HA)" || { echo "Set HA=<version> for smoke"; exit 1; }
	$(PYTHON) -m venv $(SMOKE_VENV)
	$(SMOKE_VENV)/bin/pip install -q -U pip
	$(SMOKE_VENV)/bin/pip install -q homeassistant==$(HA) aiounifi==$(AIOUNIFI)
	touch $@

clean:
	rm -rf .venv-test-* .venv-smoke-* .pytest_cache
