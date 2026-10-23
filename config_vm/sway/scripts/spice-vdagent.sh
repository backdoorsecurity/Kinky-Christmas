#!/bin/sh
# Start spice-vdagent for Sway. Sway does not activate graphical-session.target,
# so the user systemd unit never starts on its own. This build is X11-oriented
# and needs Xwayland (package: xwayland).
LOG="${XDG_RUNTIME_DIR:-/tmp}/spice-vdagent-start.log"
exec >>"$LOG" 2>&1
echo "=== $(date -Is) pid=$$ ==="
echo "DISPLAY=${DISPLAY-} WAYLAND_DISPLAY=${WAYLAND_DISPLAY-} XDG_SESSION_TYPE=${XDG_SESSION_TYPE-}"

if pgrep -x spice-vdagent >/dev/null; then
	echo "already running: $(pgrep -a spice-vdagent)"
	exit 0
fi

if [ ! -S /run/spice-vdagentd/spice-vdagent-sock ]; then
	echo "waiting for spice-vdagentd socket"
	i=0
	while [ "$i" -lt 50 ]; do
		[ -S /run/spice-vdagentd/spice-vdagent-sock ] && break
		i=$((i + 1))
		sleep 0.1
	done
fi
if [ ! -S /run/spice-vdagentd/spice-vdagent-sock ]; then
	echo "ERROR: spice-vdagentd socket missing"
	exit 1
fi

if [ -z "${DISPLAY:-}" ]; then
	export DISPLAY=:0
fi

if ! pgrep -x Xwayland >/dev/null 2>&1; then
	if ! command -v Xwayland >/dev/null 2>&1; then
		echo "ERROR: Xwayland not installed (apt install xwayland)"
		exit 1
	fi
	echo "starting Xwayland via xdpyinfo"
	timeout 3 xdpyinfo -display "$DISPLAY" >/dev/null 2>&1 || true
	i=0
	while [ "$i" -lt 50 ]; do
		pgrep -x Xwayland >/dev/null 2>&1 && break
		i=$((i + 1))
		sleep 0.1
	done
fi
echo "Xwayland: $(pgrep -a Xwayland || echo none)"
if ! pgrep -x Xwayland >/dev/null 2>&1; then
	echo "ERROR: Xwayland did not start"
	exit 1
fi

export GDK_BACKEND=x11

if [ -n "${SPICE_VDAGENT_DEBUG:-}" ]; then
	spice-vdagent -d
else
	spice-vdagent
fi
sleep 0.3
if pgrep -x spice-vdagent >/dev/null; then
	echo "started: $(pgrep -a spice-vdagent)"
	exit 0
fi
echo "ERROR: spice-vdagent failed to stay up"
exit 1
