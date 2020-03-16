# -*- coding: utf-8 -*-


import datetime, glob, json, logging, os, pprint, time
import requests, solr
# from iip_processing_app.lib.processor import Indexer


log = logging.getLogger( 'usep_gh_web_logger' )
if not logging._handlers:  # true when module accessed by queue-jobs
    logging_config_dct = json.loads( LOG_CONF_JSN )
    logging.config.dictConfig( logging_config_dct )

# indexer = Indexer()


class OrphanDeleter( object ):
    """ Contains functions for removing orphaned entries from solr.
        Helper for views.delete_solr_orphans() """

    def __init__( self ):
        """ Settings. """
        self.inscriptions_dir_path = '%s/inscriptions/' % os.environ[u'usep_gh__WEBSERVED_DATA_DIR_PATH']
        self.SOLR_URL = os.environ['usep_gh__SOLR_URL']

    # --------------------------------------------------
    # build orphan list
    # --------------------------------------------------

    def prep_orphan_list( self ) -> list:
        """ Prepares list of ids to be deleted from solr.
            Called by route list_orphans() """
        file_system_ids: list = self.build_directory_inscription_ids()
        solr_inscription_ids: list = self.build_solr_inscription_ids()
        orphans: list = self.build_orphan_list( file_system_ids, solr_inscription_ids )
        return orphans

    def build_directory_inscription_ids( self ) -> list:
        """ Returns list of file-system ids.
            Called by prep_orphan_list() """
        log.debug( 'self.inscriptions_dir_path, ```{self.inscriptions_dir_path}```' )
        inscriptions: list = glob.glob( f'{self.inscriptions_dir_path}/*.xml'  )
        log.debug( f'inscriptions (first 3), ```{pprint.pformat(inscriptions[0:3])}```...' )
        sorted_inscriptions: list = sorted( inscriptions )
        log.debug( f'sorted_inscriptions (first 3), ```{pprint.pformat(sorted_inscriptions[0:3])}```...' )
        file_system_ids = []
        for file_path in sorted_inscriptions:
            filename = file_path.split( '/' )[-1]
            inscription_id = filename.strip().split('.xml')[0]
            file_system_ids.append( inscription_id )
        log.debug( f'len(file_system_ids), `{len(file_system_ids)}`' )
        log.debug( f'file_system_ids (first 3), ```{pprint.pformat(file_system_ids[0:3])}```...' )
        return file_system_ids

    def build_solr_inscription_ids( self ) -> list:
        """ Returns list of solr inscription ids.
            Called by prep_orphan_list(). """
        url = f'{self.SOLR_URL}/select?q=*:*&fl=id&rows=100000&wt=json'
        log.debug( f'solr url, ```{url}```' )
        r = requests.get( url, timeout=15 )
        j_dict = r.json()
        docs: list = j_dict['response']['docs']  # list of dicts
        doc_list = []
        for doc in docs:
            doc_list.append( doc['id'] )
        sorted_docs = sorted( doc_list )
        log.debug( f'len(sorted_docs), `{len(sorted_docs)}`' )
        log.debug( f'sorted_docs (first 3), ```{pprint.pformat(sorted_docs[0:3])}```...' )
        return sorted_docs

    def build_orphan_list( self, directory_inscription_ids: list, solr_inscription_ids: list ) -> list:
        """ Returns list of solr-entries to delete.
            Called by prep_orphan_list(). """
        directory_set = set( directory_inscription_ids )
        solr_set = set( solr_inscription_ids )
        deletion_set = solr_set - directory_set
        orphan_list = sorted( list(deletion_set) )
        log.info( f'orphan_list, ```{pprint.pformat(orphan_list)}```' )
        return orphan_list

    # --------------------------------------------------

    def prep_context( self, data: list, orphan_handler_url: str, start_time: datetime.datetime ):
        """ Prepares response info.
            Called by route list_orphans() """
        context = {
            'data': data,
            'inscriptions_dir_path': self.inscriptions_dir_path,
            'orphan_handler_url': orphan_handler_url,
            'solr_url': self.SOLR_URL,
            'time_taken': str( datetime.datetime.now() - start_time )
        }
        log.debug( f'context, ```{pprint.pformat(context)}```' )
        return context

    def build_html( self, context: dict ):
        """ Flows data into html.
            Called by route list_orphans() """
        html = '''
<html>
    <head></head>
    <body>
'''
        log.debug( f'initial html, ```{html}```' )
        if len( context['data'] ) == 0:
            html = f'''{html}
        <p>No orphans to delete from comparing the inscription_ids in "{context['inscriptions_dir_path']}", with the inscription_ids in solr at "{context['solr_url']}".</p>
    </body>
</html>
'''
        else:
            html = f'''{html}
        <p>Comparing the inscription_ids in "{context['inscriptions_dir_path']}", with the inscription_ids in solr at "{context['solr_url']}", yields the following orphans:</p>
        <ul>
'''
            insc_html = ''
            for insc_id in context['data']:
                insc_html = f'''{insc_html}
            <li>{insc_id}</li>
'''
            html = f'''{html}{insc_html}
        </ul>
        <p>Time-taken: {context['time_taken']}</p>
        <hr/>
        <p>Would you like to delete these orphans?</p>
        <form action="{context['orphan_handler_url']}">
            <input type="submit" value="Yes" name="action_button">
            <input type="submit" value="No" name="action_button">
        </form>
    </body>
</html>
'''
        return html


    def run_deletes( self, ids_to_delete ):
        """ Runs deletions.
            Called by route '/orphan_handler/' """
        errors = []
        for delete_id in ids_to_delete:
            try:
                s = solr.Solr( self.SOLR_URL )
                time.sleep( .3 )
                response = s.delete( id=delete_id )
                s.commit()
                s.close()
                log.debug( f'id, ```{delete_id}```; response, ```{response}```' )
                # break
            except:
                errors.append( delete_id )
                log.exception( f'error trying to delete id, ```{delete_id}```; processing will continue after traceback...' )
        return errors

    ## end class OrphanDeleter()
