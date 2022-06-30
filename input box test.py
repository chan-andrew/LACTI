from tkinter import *
root = Tk()

root.title('input box')
root.geometry('1000x1000')

e = Entry(root, width = 30)
e.grid(row = 0, column = 1)

ee = Entry(root, width = 30)
ee.grid(row = 0, column = 2)

def click_me():
    mylabel = Label(root, text = 'Hello' + ' ' + e.get())
    mylabel.grid(row = 3, column = 1)
    e.delete(0, END)
    
def click_me2():
    mylabel = Label(root, text = 'Hello' + ' ' + ee.get())
    mylabel.grid(row = 3, column = 2)
    ee.delete(0, END)

mybutton = Button(root, text = 'What is your first name?',command = click_me)
mybutton.grid(row = 2, column = 1)

mybutton = Button(root, text = 'What is your last name?',command = click_me2)
mybutton.grid(row = 2, column = 2)

root.mainloop()
