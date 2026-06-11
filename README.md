how to run the SUBTOTAL Subscription Budgeter in vsc

ppen the project folder in vsc, then open the terminal and run:

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```
the requirements.txt file contains the modules "customtkinter", "matplotlib", and "werkzeug" which are
all needed to run the application. customtkinter is the ui of the application, matplotlib is what
created the pie chart when the subscription info is given, and werkzeug is a password encrypter
which encrypts the password of the account you make so anyone who has the code cannot see your
password from within it

to actually run the application, make sure the "python" extension is downloaded on the lefthand side 
where it says extensions. doing this will show a play button called run which lets runs the code
