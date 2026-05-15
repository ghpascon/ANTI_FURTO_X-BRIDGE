write_tag_example = {
	'requestBody': {
		'content': {
			'application/json': {
				'examples': {
					'target_by_epc': {
						'summary': 'Write EPC targeting by EPC',
						'description': 'Write a new EPC to a tag identified by its current EPC',
						'value': {
							'target_identifier': 'epc',
							'target_value': '000000000000000000000001',
							'new_epc': '000000000000000000000002',
							'password': '00000000',
						},
					},
					'target_by_tid': {
						'summary': 'Write EPC targeting by TID',
						'description': 'Write a new EPC to a tag identified by its TID',
						'value': {
							'target_identifier': 'tid',
							'target_value': 'e28000000000000000000001',
							'new_epc': '000000000000000000000001',
							'password': '00000000',
						},
					},
					'first_tag': {
						'summary': 'Write EPC to first tag found',
						'description': 'Write a new EPC to the first tag found (no specific target)',
						'value': {
							'target_identifier': None,
							'target_value': None,
							'new_epc': '000000000000000000000001',
							'password': '00000000',
						},
					},
				}
			}
		}
	}
}
