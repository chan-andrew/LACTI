from tkinter import *
root = Tk()

root.title('Tkinter test')
root.geometry('500x300')

my_label = Label(root, text = 'Hello!')
my_label2 = Label(root, text = 'What is your name?')

my_label.grid(row=0,column=0)
my_label2.grid(row=0,column=1)

root.mainloop()