from tkinter import *
root = Tk()

root.title('Button')
root.geometry('500x500')

def my_click():
    my_label = Label(root, text = 'Hello!', fg='#AB00FE')
    my_label.pack()

mybutton = Button(root, text = 'Click',command= my_click)
mybutton.pack()

root.mainloop()