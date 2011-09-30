Mozilla Sheriff Duty
====================

This app is all about Mozilla build engineers taking turns to be
"Sheriff". The core of this application is a roster of users and dates
which can be swapped around and repeated.
Mozilla's Playdoh is a web application template based on [Django][django].

The original requirement came from [this bug][bug].

[bug]: https://bugzilla.mozilla.org/show_bug.cgi?id=571886#c26
[django]: https://www.djangoproject.com/


Git flow
--------

Because Sheriffs is developed with the [git flow][gitflow] you'll need
to base your work off the ``develop`` branch but you'll also need the
master branch to make releases.

To get the right repositories on your computer run:

```
git clone --recursive -b develop git://github.com/mozilla/sheriffs.git
git fetch origin master:master
```

For more info, see the wiki page on [Cloning][cloning].

[cloning]: https://github.com/mozilla/sheriffs/wiki/Cloning
[gitflow]: https://github.com/nvie/gitflow

License
-------
This software is licensed under the [New BSD License][BSD]. For more
information, read the file ``LICENSE``.

[BSD]: http://creativecommons.org/licenses/BSD/

