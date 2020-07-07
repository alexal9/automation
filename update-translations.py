import openpyxl
import sys

language_map = {"English": "en_US",
				"French": "fr_FR",
				"Spanish (Castilian)": "es_ES",
				"Chinese Simplified": "zh_CN",
				"Russian": "ru_RU"
				}

header = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1">
<context>
    <name></name>'''

footer='''
</context>
</TS>'''

translation_template = '''
    <message id="{}">
        <source>{}</source>
        <translation>{}</translation>
    </message>'''

def update(spreadsheet):
	wb = openpyxl.load_workbook(spreadsheet)
	sheet = wb.active

	ids = [cell.value for cell in sheet['A'][1:]]
	# assume english is second column
	source = [cell.value for cell in sheet['B'][1:]]
	
	translation_map = {}
	for i in range(1, len(sheet['1'])):
		column = openpyxl.utils.cell.get_column_letter(i+1)
		language, *translations = [cell.value for cell in sheet[column]]
		translation_map[ language_map[language] ] = translations

	for language, translations in translation_map.items():
		with open('paxgui_' + language + '.ts', 'w') as f:
			f.write(header)
			for i in range(len(ids)):
				if source[i] and translations[i]:
					f.write( translation_template.format(ids[i], source[i], translations[i]) )
			f.write(footer)
			f.close()


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage: python update-translations.py spreadsheet')
		print('spreadsheet: excel spreadsheet file')
	else:
		update(sys.argv[-1])