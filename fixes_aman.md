
# node vversion too low conflict with vite

# install nvm 
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# relaod bash
# install newer version
nvm install 20

# start_app doesnt work could be due to too many hardcoded paths

# current run

```
cd /storage/users/projects/CarboDB-App-v2/

export INTERPROSCAN_PATH=/storage/users/job37yv/Projects/CarboDB_v3/data/dbs/interpro/interproscan-5.72-103.0/interproscan.sh

screen -S backend

conda activate carboxylase

uvicorn app.main:app --port 8091 --host 0.0.0.0 --reload

ctrl+a d

cd frontend 

npm run dev
```

# annotate.py run issue config.py module not found

changed file name from carbodb_config.py to config.py

# hardcoded file apths

trying fix using creating sm links 
in root 
```
ln -s /storage/users/job37yv/Projects/CarboDB_v3/data data
```

# cahnge the root folder in the app/pipeline/config.py

line 20, before:
```
_THIS_FILE = Path(__file__).resolve()
```

new:
```
_THIS_FILE = Path(__file__).resolve().parents[1]
```

# changed tmp file path and remove autodelete for easier debugging
```
TMP_ROOT   = ROOT / "tmp"

TMP_ROOT.mkdir(parents=True, exist_ok=True)
# NOTE: use a persistent temp folder and do not delete it automatically
tmp_path = TMP_ROOT / f"annotate_tmp_{int(time.time() * 1000)}"
tmp_path.mkdir(parents=True, exist_ok=True)

```