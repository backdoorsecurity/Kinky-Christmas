# Sway does not reparent X11 windows; Java AWT stays blank without this.
export _JAVA_AWT_WM_NONREPARENTING=1
export GTK_THEME=Swaytastic
if [ "$(tty)" = "/dev/tty1" ]; then
	exec sway --unsupported-gpu
fi
