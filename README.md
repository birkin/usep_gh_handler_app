### Purpose

Experimental code to test initiating a git_pull from a github push.


### Notes

- This app assumes a project structure like:

        enclosing_directory/
            usep_gh_handler_app/
                config/
                usep_gh_handler.py
            env_usep_gh/


- This app ssumes an entry in the apache .conf file like:

        <Directory /path/to/usep_gh_handler_app>
          Order allow,deny
          Allow from all
        </Directory>
        WSGIScriptAlias /path/to/usep_gh_handler_app/config/wsgi.py

---
