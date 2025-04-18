
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



# File Management API

## New API Endpoint: List Uploaded Files

A new API endpoint has been added to list all uploaded files in the system.

### Endpoint

```
GET /da42FH0V5PGs7Hon1YTO/YXBpL2ZpbGVzLw/
```

### Authentication

This endpoint requires authentication. You must include your authentication token or be logged in via session authentication.

### Response Format

The response will be a JSON array of file objects with the following properties:

```json
[
  {
    "name": "example.jpg",
    "path": "example.jpg",
    "url": "https://example.com/media/example.jpg",
    "size": "12.3 KB",
    "type": "image",
    "modified": "2023-06-15"
  },
  // More files...
]
```

### Response Properties

- `name`: The filename
- `path`: The relative path within the media directory
- `url`: The full URL to access the file
- `size`: The file size formatted for human readability (B, KB, MB, GB)
- `type`: The file type category ("image", "video", "audio", "document", or "other")
- `modified`: The last modified date in YYYY-MM-DD format

### Example Usage

#### Using cURL

```bash
curl -X GET "https://example.com/da42FH0V5PGs7Hon1YTO/YXBpL2ZpbGVzLw/" \
  -H "Authorization: Token your_auth_token_here"
```

#### Using JavaScript Fetch

```javascript
fetch('https://example.com/da42FH0V5PGs7Hon1YTO/YXBpL2ZpbGVzLw/', {
  method: 'GET',
  headers: {
    'Authorization': 'Token your_auth_token_here'
  },
  credentials: 'same-origin'
})
.then(response => response.json())
.then(data => {
  console.log('Files:', data);
})
.catch(error => {
  console.error('Error fetching files:', error);
});
```

### Notes

- Files are sorted by last modified date (newest first)
- This endpoint only lists files; it does not provide download functionality
- To download a file, use the URL provided in the response
- Only authenticated users can access this endpoint 