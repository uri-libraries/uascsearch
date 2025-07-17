from django.core.management.base import BaseCommand
from searchapp.models import XMLDocument
import xml.etree.ElementTree as ET
import requests, os

class Command(BaseCommand):
    help = 'Fetch and index XML files from a remote server'

    def handle(self, *args, **kwargs):
        xml_urls = ['https://example.com/data1.xml', 'https://example.com/data2.xml']
        XMLDocument.objects.all().delete()

        for url in xml_urls:
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.content)
                    text = ' '.join(elem.text for elem in root.iter() if elem.text)
                    XMLDocument.objects.create(filename=os.path.basename(url), content=text)
                    self.stdout.write(self.style.SUCCESS(f'Indexed {url}'))
                except ET.ParseError:
                    self.stdout.write(self.style.ERROR(f'Failed to parse {url}'))

