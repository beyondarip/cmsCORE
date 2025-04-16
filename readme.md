
### Setup (Fast Quick Setup for development only)


0. OPTIONAL (Fast Quick Setup):

###### setup virtual environment
note: make sure the env folder is outside the cms folder
```bash
cd ..
python -m venv env2
source env2/Scripts/activate
cd cms
pip install -r requirements.txt
```
###### then run this command to initialize
```bash
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
rm db.sqlite3  # or del db.sqlite3 on Windows
python manage.py makemigrations
python manage.py makemigrations media
python manage.py migrate
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell
python manage.py generate_articles 10;
python manage.py runserver
```


for production(kinsta)
```bash
. /opt/venv/bin/activate; python manage.py makemigrations; python manage.py makemigrations media; python manage.py migrate; echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell; python manage.py generate_articles 10
```


### List Commands


###### generate articles, user prodi
```bash
python manage.py generate_articles 10
```

#### unban user

```bash
python manage.py unban_all
```



#### requirements (winodws)
need to have zip binary
C:\Program Files\Git\mingw64\bin
copy to that dir
```
Download zip-3.0-bin.zip
In the zipped file, in the bin folder, find the file zip.exe.
Extract the file zip.exe to your mingw64 bin folder (for me: C:\Program Files\Git\mingw64\bin)
Download bzip2-1.0.5-bin.zip
In the zipped file, in the bin folder, find the file bzip2.dll
Extract bzip2.dll to your mingw64\bin folder (same folder as above: C:\Program Files\Git\mingw64\bin)
```
