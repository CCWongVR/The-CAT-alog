# The CAT-alog

Web app for the catalogging of cats using Flask / Python for the backend, SQLAlchemy as the Object-relational mapping tool, SQLite as the relational database management system, and using HTML5 / Bootstrap 4 / jQuery for the Frontend design and Google+ Oauth2.0 Sign-in for authentication and authorization purposes. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You will need:

```
Python 3
Virtual Box
Vagrant
SQLAlchemy
Flask
SQLite
Any Modern Web Browser
```
## Hosting the app

Do the following to host

### Getting in

Open cmd line where vagrant is installed and run the VM

```
vagrant up
```

Log in to the VM

```
vagrant ssh
```

Move into the shared vagrant folder

```
cd /vagrant
```

Create the database

```
python3 cat_db_setup.py
```

Populate the database with an example

```
python3 cat_examples.py
```

Host the server

```
python3 project.py
```

### Connecting...

To connect to the app hosted on your virtual machine, go to your web browser and connect to the following address

```
http://localhost:5000/
```

## Acknowledgments

* Udacity FullStack Nanodegree Program
* Official Python Documentation
* Official Flask Documentation
* Official Bootstrap 4 Documentation
* Traversy Media Youtube Channel
