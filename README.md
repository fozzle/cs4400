CS4400 Final Phase
==================

Alright guys time to knock this out. You will need the following installed:
* Python
* VirtualEnv
* Flask
* Git

Git 20second Primer
-------------------

All of you made github accounts by now. I will add you as collaborators so you can push/pull to the repo. 

    git clone git@github.com:fozzle/cs4400.git cs4400

Run that command in whatever directory you want using your Terminal. This will create the cs4400 folder, git repository, and download all the files.

If you make some changes to the code, be sure to commit them and push them so that others can retrieve them. Committing is a two step process. You add files to a staging area first:
  
    git add <filename>

Then you make a commit.
    
    git commit -m "Tell us what you changed here"

Once that's done be sure to push to the repository.

    git push

If you receive an error saying you are out of sync, use:

    git pull

To download the changes then push again.

I recommend you start off every work session with:

    git pull

Connecting to the Campus MySQL
------------------------------
It's unforunate but connecting to the provided MySQL server by our class can be a PITA. Well not really, but it's harder than just typing in the address. All of you have Macs and by extension should have ssh installed. You'll have to follow these steps in order to get the app connected from your PC to the campus MySQL.

First SSH into the sql server w/ a tunnel.
    
    ssh <your-gt-login>@academic-mysql.cc.gatech.edu -L 3306:localhost:3306

You'll be prompted w/ some text about authenticity (say yes), and asked for a password. Use your GT Login password.

You also need to set a DBPASS environment variable. Use the following command to set it up.
    
    export DBPASS=<password>

The password can be found in the README file of the server, text me if you can't find it, I'll tell you and you can write it down somewhere.

You'll have to perform these once for every time you use your PC, it'll last until you close the terminal or restart. Doesn't take long though.


You don't really need to worry about this, just FYI:

Basically this makes the MySQL available on your local port 3306, but the server thinks it's coming from itself locally. . The environment variable just holds the password that the app will use for MySQL, it's a safer way to do things rather than publish it on here.

VirtualEnv
----------
You only need to do this once. All of you installed virtualenv during our last meeting. To use it, go to the cs4400 directory we created, and use the following command:
    
    virtualenv venv

A folder venv will be created. Use this as your path with:
    
    source venv/bin/activate

You should see a little (venv) to the left of your command line location. Now you need to install our dev environment.
    
    pip install -r requirements.txt

This will take care of all dependencies and stuff. Easy right?
Once you do this once, all you need to do is:

    source venv/bin/activate

Every time you make a new terminal window. (Basically if you don't see (venv) to the left, use that to activate it)

Without venv activated, you won't be able to use Flask and test out stuff.



Flask
-----

Just read the flask documentation or follow my examples. Text or call me if you have questions I'd rather answer them then you waste hours doing nothing.


