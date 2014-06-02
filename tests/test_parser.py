# -*- coding: utf-8 -*-

import logging, pprint, unittest
from usep_gh_handler_app.utils.indexer_parser import Parser


log = logging.getLogger(__name__)


class ParserTest( unittest.TestCase ):
    """ Tests Parser functions.
            To use:
            - activate the virtual environment
            - cd to tests directory
            - run python ./test_parser.py """

    def test_init(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.xml_path == u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml', p.xml_path
        assert p.i_id == u'CA.Berk.UC.HMA.G.8-4213', p.i_id
        assert unicode(type(p.xml_doc)) == u"<type 'lxml.etree._Element'>", unicode(type(p.xml_doc))

    def test_parseBibAuthors_AuthorsMonogram(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        result = p.parseBibAuthors()
        assert result == [u'Franz, J. (ed.)', u'Smutny, R.J.'], result

    def test_parseBibAuthors_None(self):
        p = Parser(
            inscription_xml_path=u'./test_files/KY.Lou.SAM.L.1929.17.318AandB.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        result = p.parseBibAuthors()
        assert result == [], result

    def test_parseBibAuthors_Unicode(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Malibu.JPGM.G.71.AA.288.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        result = p.parseBibAuthors()
        assert result == [u'Vermeule, C. and Neuerburg', u'Pfuhl, E. and M\xf6bius, H.'], result

    def test_parseBibAuthors_someBibsWithNoAuthor(self):
        p = Parser(
            inscription_xml_path=u'./test_files/VA.Rich.MFA.G.60.23.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        result = p.parseBibAuthors()
        assert result == [u'Beazley, J.', u'Carpenter', u'Korshak, Y.', u'Schefold, K.'], result

    def test_parseBibIds_missingHash(self):
        p = Parser(
            inscription_xml_path=u'./test_files/MI.AA.UM.KM.L.1037.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseBibIds() == [u'AE_1974', u'AJA_DArms', u'Tuck'], p.parseBibIds()

    def test_parseBibIds_Single(self):
        p = Parser(
            inscription_xml_path=u'./test_files/MD.Balt.JHU.L.6.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIds()
        self.assertEqual( [u'AJP_Wilson2.1'], p.bib_ids )

    def test_parseBibIds_multiple(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIds()
        self.assertEqual( [u'CIG_III', u'Smutny'], p.bib_ids )
        p = Parser(
            inscription_xml_path=u'./test_files/KS.Lawr.UK.L.Tmp96.12.7.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIds()
        self.assertEqual( [u'AJA_Lind', u'AJA_Magoffin', u'CIL_VI'], p.bib_ids )

    def test_parseBibIds_multipleAndOneBad(self):
        p = Parser(
            inscription_xml_path=u'./test_files/MI.AA.UM.KM.L.1019bis.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIds()
        self.assertEqual( p.bib_ids, [u'AE_1988', u'CIL_X', u'Puteoli_9-10', u'Tuck'] )

    def test_parseBibIdsFiltered_multiple(self):
        p = Parser(
            inscription_xml_path=u'./test_files/KS.Lawr.UK.L.Tmp96.12.7.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIdsFiltered()
        self.assertEqual( [u'AJA', u'CIL'], p.bib_ids_filtered )

    def test_parseBibIdsFiltered_Journal(self):
        p = Parser(
            inscription_xml_path=u'./test_files/MD.Balt.JHU.L.6.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIdsFiltered()
        self.assertEqual( [u'AJP'], p.bib_ids_filtered )

    def test_parseBibIdsFiltered_duplicates(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.L.8-2330.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIdsFiltered()
        assert p.bib_ids_filtered == [u'CIL', u'LSO'], p.bib_ids_filtered    # _not_ [u'CIL', u'CIL', u'LSO']

    def test_parseBibIdsFiltered_ignoreMonograph(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIdsFiltered()
        assert p.bib_ids_filtered == [u'CIG'], p.bib_ids_filtered    # _not_ 'Smutny'

    def test_parseBibIdsFiltered_ignoreMonographB(self):
        p = Parser(
            inscription_xml_path=u'./test_files/NY.Brook.BM.G.16.89.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIdsFiltered()
        assert p.bib_ids_filtered == [u'OGIS'], p.bib_ids_filtered    # _not_ 'Michel' & 'Herbert_GLIBM'

    def test_parseBibIdsFiltered_IlsDirectMatch(self):
        p = Parser(
            inscription_xml_path=u'./test_files/MI.Detr.DIA.L.38.185.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIdsFiltered()
        assert p.bib_ids_filtered == ['CIL', 'ILS', 'ZPE'], p.bib_ids_filtered

    def test_parseBibIdsTypes(self):
        p = Parser(
            inscription_xml_path= u'./test_files/MI.AA.UM.KM.L.1019bis.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibIdsTypes()
        self.assertEqual( p.bib_ids_types, [u'corpora', u'corpora', u'journal', u'monograph'] )

    def test_parseBibTitles_AuthorMonogram(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibTitles()
        # print u'-a: %s' % p.bib_ids
        # print u'-b: %s' % p.bib_ids_filtered
        # print u'- p.bib_titles: %s' % p.bib_titles
        self.assertEqual( [u'Corpus Inscriptionum Graecarum', u'Greek and Latin Inscriptions at Berkeley'], p.bib_titles )
        self.assertEqual( [u'Corpus Inscriptionum Graecarum', u'Greek and Latin Inscriptions at Berkeley'], p.bib_titles_all )
        self.assertTrue( len(p.bib_ids) == len(p.bib_titles_all) )

    def test_parseBibTitles_JJC(self):
        '''
        bib_ids = [u'AJA_Lind', u'AJA_Magoffin', u'CIL_VI']
        bib_ids_filtered = [u'AJA', u'CIL']
        '''
        p = Parser(
            inscription_xml_path=u'./test_files/KS.Lawr.UK.L.Tmp96.12.7.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibTitles()
        self.assertEqual( [
            u'American Journal of Archaeology',
            u'Corpus Inscriptionum Latinarum',
            ], p.bib_titles )
        self.assertEqual( [
            u'American Journal of Archaeology',
            u'American Journal of Archaeology',
            u'Corpus Inscriptionum Latinarum',
            ], p.bib_titles_all )
        self.assertTrue( len(p.bib_ids) == len(p.bib_titles_all) )

    def test_parseBibTitles_unusualVolumeHierarchy(self):
        p = Parser(
            inscription_xml_path=u'./test_files/TX.Aust.UT.G.Tmp97.2.1.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibTitles()
        # print u'\nbib_ids: %s' % p.bib_ids
        self.assertEqual( [u'Zeitschrift f\xfcr Papyrologie und Epigraphik'], p.bib_titles )
        self.assertEqual( [u'Zeitschrift f\xfcr Papyrologie und Epigraphik'], p.bib_titles_all )
        self.assertTrue( len(p.bib_ids) == len(p.bib_titles_all) )

    def test_parseBibTitles_unpublished(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.SJ.Egypt.G.1744.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibTitles()
        self.assertEqual( [u'Unpublished'], p.bib_titles )
        self.assertEqual( [u'Unpublished'], p.bib_titles_all )
        self.assertTrue( len(p.bib_ids) == len(p.bib_titles_all) )

    def test_parseBibTitles_CorporaDirect_and_Duplicates(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.L.8-2330.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibTitles()
        self.assertEqual( [
            u'Corpus Inscriptionum Latinarum',
            u'Lateres Signati Ostienses I Testo; M. Steinby, Lateres Signati Ostienses II Tavole',
            u'Greek and Latin Inscriptions at Berkeley'], p.bib_titles
            )
        self.assertEqual( [
            u'Corpus Inscriptionum Latinarum',
            u'Corpus Inscriptionum Latinarum',
            u'Lateres Signati Ostienses I Testo; M. Steinby, Lateres Signati Ostienses II Tavole',
            u'Greek and Latin Inscriptions at Berkeley'], p.bib_titles_all
            )
        self.assertTrue( len(p.bib_ids) == len(p.bib_titles_all) )

    def test_parseBibTitles_UnicodeTitle(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.L.8-3420.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibTitles()
        self.assertEqual( [u"L'Ann\xe9e \xc9pigraphique", u'Greek and Latin Inscriptions at Berkeley'], p.bib_titles )
        self.assertEqual( [u"L'Ann\xe9e \xc9pigraphique", u'Greek and Latin Inscriptions at Berkeley'], p.bib_titles_all )
        self.assertTrue( len(p.bib_ids) == len(p.bib_titles_all) )

    def test_parseBibTitles_MatchBibIdCount(self):
        """ Tests handling missing <bibl> for a bib_id.
                As of Jan 10, 2014, there is no <bibl> entry for 'NSA_1892',
                    which was causing a problem in the website's Publication display. """
        p = Parser(
            inscription_xml_path=u'./test_files/MI.AA.UM.KM.L.1056.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        p.parseBibTitles()
        self.assertEqual( [u'American Journal of Archaeology',
                u'Corpus Vasorum Antiquorum',
                u'unknown',
                u'Latin Inscriptions in the Kelsey Mueum: The Dennison and De Criscio Collections'],
                p.bib_titles )
        self.assertEqual( [u'American Journal of Archaeology',
            u'Corpus Vasorum Antiquorum',
            u'unknown',
            u'Latin Inscriptions in the Kelsey Mueum: The Dennison and De Criscio Collections'],
            p.bib_titles_all )
        self.assertEqual( [u'AJA_Dennison', u'CVA_11.3', u'NSA_1892', u'Tuck'], p.bib_ids )
        self.assertTrue( len(p.bib_ids) == len(p.bib_titles_all) )

    def test_parseCondition(self):
        ## with attribute
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseCondition() == u'complete.intact', p.parseCondition()
        ## without attribute
        p = Parser(
            inscription_xml_path=u'./test_files/KY.Lou.SAM.L.1929.17.318AandB.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseCondition() == None, p.parseCondition()

    def test_parseFake(self):
        ## element found
        p = Parser(
            inscription_xml_path=u'./test_files/MA.Glouc.HCM.L.Tmp97.6.44.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        value = p.parseFake()
        assert value == u'fake' and type(value) == unicode, p.parseFake()
        ## element not found
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseFake() == None, p.parseFake()
        ## element found but empty
        p = Parser(
            inscription_xml_path=u'./test_files/MO.Col.UM.MAA.G.2011.25.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseFake() == None, p.parseFake()

    def test_parseId(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( u'CA.Berk.UC.HMA.G.8-4213', p.parseId() )

    def test_parse_graphic_name(self):
        ## with graphic element
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( u'CA.Berk.UC.HMA.G.8-4213.jpg', p.parse_graphic_name() )
        ## without graphic element
        p = Parser(
            inscription_xml_path=u'./test_files/CA.SJ.Egypt.G.1744.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( None, p.parse_graphic_name() )
        ## with multiple images
        p = Parser(
            inscription_xml_path=u'./test_files/MI.AA.UM.KM.L.1019bis.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( u'MI.AA.UM.KM.L.1019bis.jpg', p.parse_graphic_name() )
        ## with element but epty url attribute
        p = Parser(
            inscription_xml_path=u'./test_files/MO.Col.UM.MAA.G.2011.25.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( None, p.parse_graphic_name() )

    def test_parseLanguage(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( u'grc', p.parseLanguage() )
        # assert p.parseLanguage() == u'grc', p.parseLanguage()

    def test_parseMaterial(self):
        ## with data
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseMaterial() == u'stone.marble', p.parseMaterial()
        ## without data
        p = Parser(
            inscription_xml_path=u'./test_files/MI.Detr.DIA.L.38.185.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseMaterial() == None, p.parseMaterial()

    def test_parseMsidRegion(self):    # msid parsers are listed logically
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseMsidRegion() == u'CA', p.parseMsidRegion()
        assert isinstance(p.msid_region, unicode), type(p.msid_region)

    def test_parseMsidSettlement(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseMsidSettlement() == u'Berk', p.parseMsidSettlement()
        assert isinstance(p.msid_settlement, unicode), type(p.msid_settlement)

    def test_parseMsidInstitution(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseMsidInstitution() == u'UC', p.parseMsidInstitution()
        assert isinstance(p.msid_institution, unicode), type(p.msid_institution)

    def test_parseMsidRepository(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseMsidRepository() == u'HMA', p.parseMsidRepository()
        assert isinstance(p.msid_repository, unicode), type(p.msid_repository)

    def test_parseMsidIdno(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseMsidIdno() == u'8/4213', p.parseMsidIdno()
        assert isinstance(p.msid_idno, unicode), type(p.msid_idno)

    def test_parseStatus(self):
        ## metadata
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( u'metadata', p.parseStatus() )
        self.assertEqual( unicode, type(p.status) )
        ## transcription
        p = Parser(
            inscription_xml_path=u'./test_files/MA.Glouc.HCM.L.Tmp97.6.44.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( u'transcription', p.parseStatus() )
        self.assertEqual( unicode, type(p.status) )
        ## bib_only
        p = Parser(
            inscription_xml_path=u'./test_files/MI.Detr.DIA.L.38.185.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        self.assertEqual( u'bib_only', p.parseStatus() )
        self.assertEqual( unicode, type(p.status) )

    def test_parseTitle(self):
        p = Parser(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml',
            log=log )
        assert p.parseTitle() == u'CA.Berk.UC.HMA.G.8/4213', p.parseTitle()

    # end class ParserTest()




if __name__ == "__main__":
    unittest.TestCase.maxDiff = None    # allows error to show in long output
    unittest.main()
