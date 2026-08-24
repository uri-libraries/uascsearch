import xml.etree.ElementTree as ET

from django.test import SimpleTestCase

from search_app.management.commands.index_xml import Command


class MetadataExtractionTests(SimpleTestCase):
	def test_extract_all_metadata_preserves_nested_elements_and_attributes(self):
		root = ET.fromstring(
			'<ead xmlns="urn:isbn:1-931666-22-9">'
			'<archdesc level="collection">'
			'<did><unittitle>Example Collection</unittitle></did>'
			'<scopecontent><p>Scope text</p></scopecontent>'
			'</archdesc>'
			'</ead>'
		)

		metadata = Command().extract_all_metadata(root)
		elements = metadata['elements']

		self.assertEqual(elements[0]['path'], '/ead')
		self.assertEqual(elements[0]['attributes'], {})
		self.assertEqual(elements[1]['attributes'], {'level': 'collection'})
		self.assertEqual(
			next(item['value'] for item in elements if item['name'] == 'scopecontent'),
			'Scope text',
		)
		self.assertEqual(
			next(item['path'] for item in elements if item['name'] == 'unittitle'),
			'/ead/archdesc/did/unittitle',
		)

	def test_build_dublin_core_maps_rich_ead_fields(self):
		extracted_fields = {
			'title': 'Example Collection',
			'creator': 'Example Creator',
			'dates': '1950-1960',
			'abstract': 'Collection abstract',
			'eadid': 'MS001',
			'public_url': 'https://example.org/finding-aid',
		}
		metadata = {
			'elements': [
				{'name': 'bioghist', 'value': 'Biographical history'},
				{'name': 'scopecontent', 'value': 'Scope and contents'},
				{'name': 'language', 'value': 'English'},
				{'name': 'subject', 'value': 'Archives'},
			]
		}

		dublin_core = Command().build_dublin_core(extracted_fields, metadata)

		self.assertEqual(dublin_core['title'], ['Example Collection'])
		self.assertIn('Biographical history', dublin_core['description'])
		self.assertIn('Scope and contents', dublin_core['description'])
		self.assertEqual(dublin_core['language'], ['English'])
		self.assertEqual(dublin_core['identifier'], ['MS001'])
		self.assertEqual(dublin_core['source'], ['https://example.org/finding-aid'])
		self.assertEqual(dublin_core['subject'], ['Archives'])
