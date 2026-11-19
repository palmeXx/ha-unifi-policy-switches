# Run the tests against different Home Assistant and aiounifi versions.
#
#   make test HA=2026.10.4                     test suite
#   make smoke HA=2026.11.1                    import and rule filter check only
#   make test HA=2026.10.4 AIOUNIFI=96         with another aiounifi version
#   make versions                              HA pin of the newest phcc releases
#   make versions HA=2026.11.1                 aiounifi pin and matching phcc
#   make release-check                         release check of a pull request
#   make release-notes                         preview the release notes
#
# The test suite needs the pytest-homeassistant-custom-component (phcc) release
# pinning that Home Assistant version, `test` looks it up and fails without one.
# `smoke` runs without phcc, for Home Assistant versions without a release.
# AIOUNIFI defaults to the version pinned by the UniFi integration of HA.
# Each version combination gets its own virtual environment, the versions are
# only looked up when it is created.

PYTHON ?= python3.14
HA ?=
AIOUNIFI ?=
PYTEST_ARGS ?=

VENV_SUFFIX = ha$(HA)$(if $(AIOUNIFI),-aiounifi$(AIOUNIFI))
TEST_VENV = .venv-test-$(VENV_SUFFIX)
SMOKE_VENV = .venv-smoke-$(VENV_SUFFIX)
VERSIONS = $(PYTHON) -I scripts/versions.py

# Shell snippet setting $aiounifi to AIOUNIFI or the pin of HA
LOOKUP_AIOUNIFI = aiounifi="$(AIOUNIFI)"; \
	if [ -z "$$aiounifi" ]; then aiounifi=$$($(VERSIONS) aiounifi --ha $(HA)) || exit 1; fi

.PHONY: help require-ha test smoke versions release-check release-notes clean

help:
	@sed -n '2,16s/^# \{0,1\}//p' Makefile

require-ha:
	@test -n "$(HA)" || { echo "Set HA=<version>, e.g. make $(MAKECMDGOALS) HA=2026.10.4, see make versions"; exit 1; }

test: require-ha $(TEST_VENV)/.installed
	$(TEST_VENV)/bin/pytest $(PYTEST_ARGS)

smoke: require-ha $(SMOKE_VENV)/.installed
	$(SMOKE_VENV)/bin/python scripts/smoke_test.py

$(TEST_VENV)/.installed:
	@phcc=$$($(VERSIONS) phcc --ha $(HA)) || exit 1; \
	$(LOOKUP_AIOUNIFI); \
	echo "Home Assistant $(HA), pytest-homeassistant-custom-component $$phcc, aiounifi $$aiounifi"; \
	$(PYTHON) -m venv $(TEST_VENV) && \
	$(TEST_VENV)/bin/pip install -q -U pip && \
	$(TEST_VENV)/bin/pip install -q \
		pytest-homeassistant-custom-component==$$phcc aiounifi==$$aiounifi
	touch $@

$(SMOKE_VENV)/.installed:
	@$(LOOKUP_AIOUNIFI); \
	echo "Home Assistant $(HA), aiounifi $$aiounifi"; \
	$(PYTHON) -m venv $(SMOKE_VENV) && \
	$(SMOKE_VENV)/bin/pip install -q -U pip && \
	$(SMOKE_VENV)/bin/pip install -q homeassistant==$(HA) aiounifi==$$aiounifi
	touch $@

# Standard library only, runs without a virtual environment
versions:
	@$(if $(HA),$(VERSIONS) show --ha $(HA),$(VERSIONS) list $(if $(COUNT),--count $(COUNT)))

# Same check as on pull requests, BASE=main to compare with the local branch
BASE ?= origin/main
release-check:
	$(PYTHON) -I scripts/release.py check --base $(BASE)

# Notes of the working tree version, REF=<tag> for an existing release
release-notes:
	$(PYTHON) -I scripts/release.py notes $(if $(REF),--ref $(REF))

clean:
	rm -rf .venv-test-* .venv-smoke-* .pytest_cache
