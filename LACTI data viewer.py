#import all needed libraries
from tkinter import *
from tkinter import filedialog
from PIL import ImageTk, Image
import check_data

# function for opening folders
def browseFiles():
    # filename = filedialog.askopenfilename(initialdir = "/",
                                        #   title = "Select a File",
                                        #   filetypes = (("*.csv*", \
                                        #    "*.dat*"),("all files","*.*")))
    foldername = filedialog.askdirectory(initialdir='/',
                                         title="Select Data Folder")
    # save the foldername somehow
    # send the foldername to check_contents()
    data_paths = check_data.check_contents(foldername)
    if len(data_paths) == 0:
        print('Must have only one dat and one log file in the same directory')
        label_file_explorer.configure(text='Please select a data folder' + \
                                      ' that contains 1 .dat and 1 .csv file')
        # make this label RED
    # Change label contents
    else:
        label_file_explorer.configure(text="Folder Opened: " + foldername)
        # proceed to check_data.check_data(foldername)
        # open the 2nd figure


# Create the root window
window = Tk()

# Set window title
window.title('Data Viewer')

# Set window size
window.geometry("700x500")

#Set window background color
window.config(background = "white")

# Create a File Explorer label
label_file_explorer = Label(window, text = "Select Browse Files to select files. Select Exit to exit the application.", width = 100, height = 4, fg = "blue")
button_explore = Button(window, text = "Select Data Folder", command = browseFiles)
button_exit = Button(window, text = "Exit", command = exit)

# placement of buttons using grids
label_file_explorer.grid(column = 1, row = 1)
button_explore.grid(column = 1, row = 2)
button_exit.grid(column = 1,row = 3)


frame = Frame(window, width=100, height=50)

frame.place(anchor='center', relx=0.25, rely=0.25)

# Create an object of tkinter ImageTk
# img = ImageTk.PhotoImage(Image.open("PennMedicineLogo.png"))

# Create a Label Widget to display the text or Image
# label = Label(frame, image = img)
# label.pack()

window.mainloop()
  
window.mainloop()