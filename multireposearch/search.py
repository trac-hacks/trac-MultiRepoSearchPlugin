from trac.admin.api import IAdminCommandProvider
from trac.core import *
from trac.config import *
from trac.search import ISearchSource, shorten_result
from trac.perm import IPermissionRequestor
from trac.mimeview.api import Mimeview
from trac.versioncontrol import RepositoryManager
from trac.versioncontrol.api import Node, IRepositoryChangeListener

from multireposearch.interfaces import IMultiRepoSearchBackend

class MultiRepoSearchPlugin(Component):
    """ Search the source repository. """
    implements(ISearchSource, IPermissionRequestor,
               IAdminCommandProvider,
               IRepositoryChangeListener)


    search_backend = ExtensionOption(
        'multireposearch', 'search_backend',
        IMultiRepoSearchBackend,
        'SqlIndexer',
        "Name of the component implementing `IMultiRepoSearchBackend`, "
        "which implements repository indexing and search strategies.")

    def reindex_all(self, verbose=False):
        repos = RepositoryManager(self.env).get_all_repositories()
        for reponame in repos:
            self.search_backend.reindex_repository(reponame, verbose=verbose)

    ## methods for IRepositoryChangeListener
    def changeset_added(self, repos, changeset):
        self.search_backend.reindex_repository(repos.reponame)

    def changeset_modified(self, repos, changeset, old_changeset):
        # TODO: not realy sure what to do here but i think we can ignore it,
        # because changeset modifications can only pertain to commit-metadata 
        # which we don't care about
        pass

    ### methods for IAdminCommandProvider

    """Extension point interface for adding commands to the console
    administration interface `trac-admin`.
    """

    def get_admin_commands(self):
        """Return a list of available admin commands.
        
        The items returned by this function must be tuples of the form
        `(command, args, help, complete, execute)`, where `command` contains
        the space-separated command and sub-command names, `args` is a string
        describing the command arguments and `help` is the help text. The
        first paragraph of the help text is taken as a short help, shown in the
        list of commands.
        
        `complete` is called to auto-complete the command arguments, with the
        current list of arguments as its only argument. It should return a list
        of relevant values for the last argument in the list.
        
        `execute` is called to execute the command, with the command arguments
        passed as positional arguments.
        """
        return [
            ('multireposearch reindex_all', '', 'reindex all known repositories', 
             None,
             lambda: self.reindex_all(verbose=True)),
            ('multireposearch reindex', 'reponame', 'reindex a single repository', 
             None, 
             lambda reponame: self.search_backend.reindex_repository(reponame, verbose=True)),
            ]
    

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'REPO_SEARCH'

    # ISearchSource methods
    def get_search_filters(self, req):
        if req.perm.has_permission('REPO_SEARCH'):
            yield ('repo', 'Source Repository', 1)

    def get_search_results(self, req, query, filters):
        if 'repo' not in filters:
            return

        for filename, reponame in self.search_backend.find_words(query):
            repo = self.env.get_repository(reponame=reponame, authname=req.authname)
            node = repo.get_node(filename)

            if node.kind == Node.DIRECTORY:
                yield (self.env.href.browser(reponame, filename),
                       "%s (in %s)" % (filename, reponame), change.date, change.author,
                       'Directory')
            else:
                found = 0
                mimeview = Mimeview(self.env)
                content = mimeview.to_unicode(node.get_content().read(), node.get_content_type())
                for n, line in enumerate(content.splitlines()):
                    line = line.lower()
                    for q in query:
                        idx = line.find(q)
                        if idx != -1:
                            found = n + 1
                            break
                    if found:
                        break

                change = repo.get_changeset(node.rev)

                yield (self.env.href.browser(reponame, filename
                                             ) + (found and '#L%i' % found or ''
                                                  ),
                       "%s (in %s)" % (filename, reponame), change.date, change.author,
                       shorten_result(content, query))

