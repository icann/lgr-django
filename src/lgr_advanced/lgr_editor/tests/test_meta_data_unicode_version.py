from lgr_advanced.lgr_editor.forms import MetadataForm
from lgr_models.tests.test_unicode_version import TestUnicodeVersion


class TestMetaDataUnicodeVersion(TestUnicodeVersion):

    def test_unicode_versions(self):
        """
        Verify the list displayed is unfiltered and contains all supported versions
        """
        self.a_unicode_version.activated = True
        self.a_unicode_version.save()
        metadata_form = MetadataForm(additional_repertoires=[], disabled=False,
                                     initial={'version': '1', 'version_comment': 'Sample LGR for French',
                                              'date': '2015-08-07', 'language': 'fr', 'scope': 'example',
                                              'scope_type': 'domain', 'unicode_version': '6.3.0',
                                              'validity_start': None, 'validity_end': None,
                                              'description': 'This is a basic LGR sample for the French language. It does not aim to be complete or accurate but only to provide an example.',
                                              'description_type': 'text/plain', 'validating_repertoire': [('', '')]})
        self.assertSetEqual(set(metadata_form.fields['unicode_version'].choices),
                            {(self.a_unicode_version.version, self.a_unicode_version.version)})
