import tkinter as tk

class ToolTip:
    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay  # Delay in milliseconds
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        
    def show_tip(self):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 0
        y += self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        tip_width = self.widget.winfo_width()
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="black", foreground="white",
                         relief=tk.SOLID, borderwidth=1,
                         font=("宋体", "9"), wraplength=tip_width)
        label.pack(ipadx=1)
        
    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()
            
    def schedule_show_tip(self, event):
        self.id = self.widget.after(self.delay, self.show_tip)
        
    def schedule_hide_tip(self, event):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hide_tip()

def create_tooltip(widget, text, delay=500):
    tool_tip = ToolTip(widget, text, delay)
    widget.bind("<Enter>", tool_tip.schedule_show_tip)
    widget.bind("<Leave>", tool_tip.schedule_hide_tip)
