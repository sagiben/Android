# Android utilities

* changelog.py - AOSP [repo](https://source.android.com/source/developing.html) subcommand for creating AOSP projects changelog between revisions.

  - **Installation** : copy the script to /path/to/.repo/subcmds
  - **Usage** : 
    ```
    Usage: repo changelog [<options>] [--revisions=<revision range>] [<project>...]

    Options:
      -h, --help            show this help message and exit
      -r, --regex           Execute the command only on projects matching regex or
                            wildcard expression

    Output:
      -v, --verbose         Show command error messages
      --revisions=REVISIONS Revisions range
    -l SUBSCRIBERS, --list=SUBSCRIBERS
                            A file holding the subscribers list in JSON format
    ```



