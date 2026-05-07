import tkinter as tk
from tkinter import colorchooser

class Drawing:

    def __init__(self,root):
        self.root=root
        self.root.title("Drawing Space")

        # toolbar
        toolbar=tk.Frame(root,bg="lightgray",pady=5)
        toolbar.pack(fill=tk.X)

        # Color picker button
        tk.Label(toolbar, text="Color:", bg="lightgray").pack(side=tk.LEFT, padx=5)
        self.color_btn = tk.Button(toolbar, bg="black", width=3, command=self.pick_color)
        self.color_btn.pack(side=tk.LEFT, padx=5)


        # Thickness
        tk.Label(toolbar,bg="lightgray",text="Thickness").pack(side=tk.LEFT,padx=5)
        self.thickness = tk.Scale(toolbar, from_=1, to=20, orient=tk.HORIZONTAL, bg="lightgray")
        self.thickness.set(3)
        self.thickness.pack(side=tk.LEFT, padx=5)


        # Tool buttons
        self.tool = "pen"
        self.pen_btn = tk.Button(toolbar, text="Pen", width=6, command=self.use_pen)
        self.pen_btn.pack(side=tk.LEFT, padx=5)
 
        self.eraser_btn = tk.Button(toolbar, text="Eraser", width=6, command=self.use_eraser)
        self.eraser_btn.pack(side=tk.LEFT, padx=5)
 
        tk.Button(toolbar, text="Undo", width=6, command=self.undo).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Clear", width=6, command=self.clear).pack(side=tk.LEFT, padx=5)


        # setting up canvas for width and height
        self.canvas= tk.Canvas(root, bg="white",width=800,height=600)
        self.canvas.pack(fill=tk.BOTH,expand=True)

        # binding button on drawing app canvas
        self.canvas.bind("<Button-1>",self.start_drawing)
        self.canvas.bind("<B1-Motion>",self.draw)
        self.canvas.bind("<ButtonRelease-1>",self.stop_drawing)

        self.current_color="black"
        self.last_x=None
        self.last_y=None
        self.history=[]

        self.update_buttons()

    def pick_color(self):
        color=colorchooser.askcolor(color=self.current_color)[1]
        if color:
            self.current_color = color
            self.color_btn.config(bg=color)

    # when drawing 
    def start_drawing(self,event):
        self.last_x=event.x
        self.last_y=event.y
        self.history.append([])

    def use_pen(self):
        self.tool="pen"
        self.update_buttons()

    def use_eraser(self):
        self.tool="eraser"
        self.update_buttons()
        
    def update_buttons(self):
        self.pen_btn.config(relief=tk.SUNKEN if self.tool == "pen" else tk.RAISED)
        self.eraser_btn.config(relief=tk.SUNKEN if self.tool == "eraser" else tk.RAISED)

    def undo(self):
        if self.history:
            ids = self.history.pop()
            for i in ids:
                self.canvas.delete(i)

    
    
    def draw(self,event):
        if self.last_x is not None and self.last_y is not None:
            color="white" if self.tool == "eraser" else self.current_color
            size =self.thickness.get()* 4 if self.tool == "eraser" else self.thickness.get()
            line=self.canvas.create_line(
                self.last_x,self.last_y,event.x,event.y,
                fill=color,width=size,capstyle=tk.ROUND, smooth=True
            )
            if self.history:
                self.history[-1].append(line)
            
            self.last_x=event.x
            self.last_y=event.y

    # if you stop strawing
    def stop_drawing(self, event):
        self.last_x=None
        self.last_y=None

    # clear canvas function
    def clear(self):
        self.canvas.delete("all")
        self.history.clear()

if __name__ == "__main__":
    root =tk.Tk()
    app =Drawing(root)
    root.mainloop()
