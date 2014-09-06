### Purpose

Listener for a github usep-data push. Flow...

- github hits flask listener on usep-data update
- listener hits dev-server if needed
- listener determines files-to-process (update & remove)
- listener initiates job `utils.processor.run_call_git_pull`
- which initiates job `utils.processor.run_copy_files`
- which initiates job `utils.indexer.run_update_index`
- which initiates 2 jobs:
    - `utils.indexer.run_update_entry` (if needed) (and which does nothing further)
    - `utils.indexer.run_remove_entry` (if needed) (and which does nothing further)


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
