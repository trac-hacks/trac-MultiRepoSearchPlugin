from trac.core import Interface

class IMultiRepoSearchBackend(Interface):
    """
    A mechanism that can be queries for full-text search on a single Trac source repository.

    A backend can also optionally provide a indexing facilities.
    """

    def reindex_repository(reponame):
        """
        Reindex a single repository if the backend deems it necessary
        """

    def find_words(query):
        """
        Yield a series of filenames which match the given query
        """

