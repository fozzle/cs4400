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

VirtualEnv
----------
You only need to do this once. All of you installed virtualenv during our last meeting. To use it, go to the cs4400 directory we created, and use the following command:
    
    virtualenv venv

A folder venv will be created. Use this as your path with:
    
    source venv/bin/activate

You should see a little (venv) to the left of your command line location. Now you need to install Flask.
    
    pip install flask

This will take care of all dependencies and stuff. Easy right?
Once you do this once, all you need to do is:

    source venv/bin/activate

Every time you make a new terminal window. (Basically if you don't see (venv) to the left, use that to activate it)

Without venv activated, you won't be able to use Flask and test out stuff.

Flask
-----

Just read the flask documentation or follow my examples. Text or call me if you have questions I'd rather answer them then you waste hours doing nothing.


