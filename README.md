# Item Catalog

A web application in python that provides a list of items within a variety of categories and integrate third party user registration and authentication. 
Authenticated users have the ability to add new items and categories. Also edit and delete their own items.

## Set Up

1. Clone the [fullstack-nanodegree-vm repository](https://github.com/udacity/fullstack-nanodegree-vm).

2. Look for the *catalog* folder and replace it with the contents of this respository.

## Usage

Launch the Vagrant VM from inside the *vagrant* folder with:

`vagrant up`

Then access the shell with:

`vagrant ssh`

Then move inside the catalog folder:

`cd /vagrant/catalog`

To preload the database with contents:

`python catagoriesanditems.py`

To run the application:

`python view.py`

After the last command you are able to browse the application at this URL:

`http://localhost:8000/`
