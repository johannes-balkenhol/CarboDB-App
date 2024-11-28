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
- new requirements can be added by ``conda list -e > requirements.txt``
#### Frontend
- in terminal from project root ``cd frontend``
- [See frontend README.md](frontend/README.md)

### General project structure

### Tests
Tests are implemented using ``pytest``. This command can be run to start the test suit.\
To get a more detailed output use ``pytest -v``.
