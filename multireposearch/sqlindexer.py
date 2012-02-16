import posixpath
from trac.core import *
from trac.db import Table, Column, Index, DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.mimeview.api import Mimeview
from trac.search.api import search_to_sql
from trac.versioncontrol.api import Node

from tracsqlhelper import get_scalar, execute_non_query, create_table

from multireposearch.interfaces import IMultiRepoSearchBackend
class SqlIndexer(Component):
    
    implements(IMultiRepoSearchBackend, 
               IEnvironmentSetupParticipant)

    ## internal methods
    def _last_known_rev(self, reponame):
        indexed_rev = get_scalar(self.env,
                                 "SELECT version FROM repository_version WHERE repo=%s",
                                 0, reponame)
        return indexed_rev

    def _walk_repo(self, repo, path):
        node = repo.get_node(path)
        basename = posixpath.basename(path)

        if node.kind == Node.DIRECTORY:
            for subnode in node.get_entries():
                for result in self._walk_repo(repo, subnode.path):
                    yield result
        else:
            yield node

    query = """
SELECT id, filename, repo
FROM repository_node
WHERE %s
"""
    
    ## methods for IMultiRepoSearchBackend

    def reindex_repository(self, reponame, verbose=False):
        repo = self.env.get_repository(reponame=reponame)

        last_known_rev = self._last_known_rev(reponame)
        if last_known_rev is not None and last_known_rev == repo.youngest_rev:
            if verbose: print "Repo %s doesn't need reindexing" % reponame
            return

        if verbose: print "Repo %s DOES need reindexing" % reponame
        mimeview = Mimeview(self.env)

        @self.env.with_transaction()
        def do_reindex(db):
            cursor = db.cursor()

            for node in self._walk_repo(repo, "/"):
                if verbose: print "Fetching content at %s" % node.path
                content = node.get_content()
                if content is None:
                    continue
                content = mimeview.to_unicode(content.read(), node.get_content_type())

                cursor.execute("""
DELETE FROM repository_node
WHERE repo=%s AND filename=%s""", [reponame, node.path])
                cursor.execute("""
INSERT INTO repository_node (repo, filename, contents)
VALUES (%s, %s, %s)""", [reponame, node.path, content])
                
            if last_known_rev is None:
                cursor.execute("""
INSERT INTO repository_version (repo, version)
VALUES (%s, %s)""", [reponame, repo.youngest_rev])
            else:
                cursor.execute("""
UPDATE repository_version 
SET version=%s
WHERE repo=%s""", [repo.youngest_rev, reponame])


    def find_words(self, query):
        db = self.env.get_read_db()
        sql, args = search_to_sql(db, ['contents'], query)
        cursor = db.cursor()
        cursor.execute(self.query % sql, args)
        for id, filename, repo in cursor:
            yield filename, repo


    ### methods for IEnvironmentSetupParticipant    
    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""
    
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
    
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        return not self.version()

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        if not self.environment_needs_upgrade(db):
            return

        version = self.version()
        for version in range(self.version(), len(self.steps)):
            for step in self.steps[version]:
                step(self)
        execute_non_query(self.env,
                          "update system set value='1' where name='multireposearch.sqlindexer.db_version';")


    def version(self):
        """returns version of the database (an int)"""
        version = get_scalar(self.env, 
                             "select value from system where name = 'multireposearch.sqlindexer.db_version';")
        if version:
            return int(version)
        return 0
        
    def create_db(self):
        repo_cache_table = Table('repository_node', key=('id'))[
            Column('id', auto_increment=True),
            Column('repo'),
            Column('filename'),
            Column('contents'),
            Index(['contents']),
            ]
        create_table(self.env, repo_cache_table)

        repo_version_table = Table('repository_version', key=('id'))[
            Column('id', auto_increment=True),
            Column('repo'),
            Column('version'),
            ]
        create_table(self.env, repo_version_table)

        execute_non_query(self.env, "insert into system (name, value) values ('multireposearch.sqlindexer.db_version', '1');")

    # ordered steps for upgrading
    steps = [ 
        [ create_db ],
        ]


