# udacity-multi-user-blog

'Multi-user Blog' is the final project for the course 'Intro to Backend'. Here, the registered users can post blogs and comments, and as well as upvoting a blog of their choice. Basically, it is a scaled-down, primitive version of Reddit.

The program uses Google App Engine, Google Datastore, Jinja2, Python, HTML5, CSS3, Javscript and jQuery. 

## Dependencies

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
4. Type `git clone https://github.com/hyungmogu/udacity-multi-user-blog` in a directory of choice; download the repository
5. Open and follow instructions in `udacity-multi-user-blog/'Multi-user Blog'/SECRET.json` using any text editors
6. Save file and quit

### Setup (Windows)
1. Download and install all dependencies
2. Install git following [this instruction](https://www.atlassian.com/git/tutorials/install-git) 
3. Open command line
4. Type `git clone https://github.com/hyungmogu/udacity-multi-user-blog` in a directory of choice; download the repository
5. Open and follow instructions in `udacity-multi-user-blog/'Multi-user Blog'/SECRET.json` using any text editors
6. Save file and quit

### Running Application on Local Machine
1. Open terminal/gcloud SDK 
2. Type `dev_appserver.py app.yaml` in `Multi-user Blog` folder; wait until gcloud sets up local server

### Stopping Local Server
1. Press `Ctrl` + `C` in terminal/gcloud SDK where the server is being run

### Deploying Application to Server
1. Create project in [console.developers.google.com](https://console.developers.google.com/)
2. Open terminal/gcloud SDK
3. Navigate to the project folder (`udacity-multi-user-blog/'Multi-user Blog'`)
4. Type `gcloud init`; initialize the configuration with gcloud
5. Type `gcloud app deploy app.yaml index.yaml`; finish deploying application to server

### Viewing Demo
1. Open a web browser (Chrome is strongly suggested)
2. Type `https://udacity-multiuser-blog-4.appspot.com/blog` in the address bar
  - For those of who are running the app on local machine, type `http://localhost:8080/blog/` instead
  - For those of who've deployed the app, type `http://<GCLOUD_PROJECDT_NAME>.appspot.com/blog` instead





