To install:

{{{
pip install -r requirements.txt
python setup.py develop
}}}

Add to your trac.conf:
{{{
[components]
multireposearch.* = enabled
}}}

Upgrade your trac environment:
{{{
trac-admin path/to/env upgrade
}}}

Prepare all available repositories with an initial indexing:
{{{
trac-admin path/to/env multireposearch reindex_all
}}}

You will now be able to perform text searches of repository contents through the trac search UI.

As long as you have your trac post-commit or post-receive hooks properly configured, 
source will remain up-to-date.

Otherwise, to manually reindex a single repository, you ca run:
{{{
trac-admin path/to/env multireposearch reindex repo-name
}}}

Where repo-name is the name assigned to your repository in Trac.
