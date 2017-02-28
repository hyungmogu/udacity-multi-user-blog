# udacity-multi-user-blog

'Multi-user Blog' is the final project for the course 'Intro to Backend'. Here, the registered users can post blogs and comments, and as well as upvoting a blog of their choice. Basically, it is a scaled-down, primitive version of Reddit.

The program uses Google App Engine, Google Datastore, Jinja2, Python, HTML5, CSS3, Javscript and jQuery. 

## Dependencies

*Note*: This file is compatible with the latest version of dependencies (Last checked: 02/28/2017).

- python 2.7.6
- gcloud
  - Google Cloud SDK 145.0.0
  - app-engine-python 1.9.50
  - bq 2.0.24
  - bq-nix 2.0.24
  - core 2017.02.21
  - core-nix 2016.11.07
  - gcloud-deps 2017.02.21
  - gsutil 4.22
  - gsutil-nix 4.18

## Getting Started

### Setup (Linux / Mac OS X)
1. Open terminal
2. Download and install all dependencies
3. Install git following [this instruction](https://www.atlassian.com/git/tutorials/install-git)
4. Navigate to a directory of choice
5. Type `git clone https://github.com/hyungmogu/udacity-multi-user-blog`; download the repository
6. Type `cd 'udacity-multi-user-blog/'Multi-user Blog'`; get inside the project folder 
7. Open and follow instructions in `SECRET.json`; finish setting up encryption for user id in cookie.
8. Save file and quit

### Setup (Windows)
1. Download and install all dependencies
2. Install git following [this instruction](https://www.atlassian.com/git/tutorials/install-git) 
3. Open command line
4. Navigate to a directory of choice
5. Type `git clone https://github.com/hyungmogu/udacity-multi-user-blog`; download the repository
6. Open gcloud sdk
7. Navigate to the folder containing the downloaded repository
6. Type `cd 'udacity-multi-user-blog/'Multi-user Blog'`; get inside the project folder
7. Open and follow instructions in `SECRET.json`; finish setting up encryption for user id in cookie.
8. Save file and quit

### Running Application on Local Machine
1. Type `dev_appserver.py app.yaml` in `Multi-user Blog` folder; activate the server

### Stopping Local Server
1. Press `Ctrl` + `C` in the terminal/gcloud where the server is being run

### Viewing Demo
1. Open a web browser (Chrome is strongly suggested)
2. Type `https://udacity-multiuser-blog-4.appspot.com/blog` in the address bar
  - For those of who are running the app on local machine, type `http://localhost:8080/blog/` instead





