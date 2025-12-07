# Carboxylase_Server
## Getting started as a developer
### Software prerequisites
- ``miniconda`` or ``anaconda`` installation

### Get the contents of the remote repository 
- Make sure you have a GitHub account and access to the repository.
- Create yourself a personal access token (this can be used with your GitHub username for authentication)
- Use ``git clone`` to fetch the repo.
- Install dependencies

### Install requirements
#### Backend
- in terminal from project root ``cd backend``
- ``conda install --file requirements.txt``
- currently used conda channels: ``defaults, conda-forge, bioconda, anaconda``
- channels can be added by ``conda config --add channels new_channel``
- new requirements can be added by ``conda list -e > requirements.txt``
#### Frontend
- in terminal from project root ``cd frontend``
- [See frontend README.md](frontend/README.md)

## General project structure

### Backend
- config.py: configures basic properties of the app
- main.py: runs the app

#### App
- \_\_init\_\_.py: contains information about the app initialization 
e.g. the scheduler to delete contents from the user data folder
- routes.py: contains the api endpoints of the app
- tasks.py: contains general tasks not associated with a particular search method
- utils.py: utility functions
#### Carboxylase_search
- contains functionalities for running the searches grouped by search
- within each search there are utility functions, the actual use case for the search
and 
- the task that is run when their api endpoint is called
- validate_user_input: contains functionalities to validate user input (fasta format)
- contains the task to run all searches as well as some utils and pdf-export on top level
#### Data_acquistion
- contains a script that can collect predicted protein sequences from EMBL-EBI
#### Domain
- contains objects of the domain e.g. defines the properties of search results
#### Repository
- repositories for data used by the searches
#### Tests
Tests are implemented using ``pytest``. This command can be run to start the test suit.\
To get a more detailed output use ``pytest -v``.
### Frontend
- [See frontend README.md](frontend/README.md)
### Resources
- contains resources like the HMM profiles, the prosite scan script and other information
collected by Dila Piri




